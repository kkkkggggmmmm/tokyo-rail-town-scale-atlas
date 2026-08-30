#!/usr/bin/env python3
"""Verify Phase 1 G0/G1 manifests against the local immutable bytes."""

from __future__ import annotations

import argparse
from pathlib import Path, PurePosixPath
import sys
from urllib.parse import urlparse
from zipfile import ZipFile

import pyarrow.parquet as pq
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_source_lock import ROOT, expand_artifacts, load_yaml, parse_headers, sha256


ALLOWED_HOSTS = {"nlftp.mlit.go.jp", "www.e-stat.go.jp"}
TEXT_KINDS = {"text"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def safe_raw_path(relative: str) -> Path:
    path = ROOT / relative
    raw_root = (ROOT / "data/raw/phase1").resolve()
    require(raw_root in path.resolve().parents, f"Path outside raw root: {relative}")
    return path


def verify_zip(path: Path) -> list[dict[str, object]]:
    rows = []
    with ZipFile(path) as archive:
        require(archive.testzip() is None, f"ZIP CRC failure: {path}")
        for sequence, info in enumerate(archive.infolist(), start=1):
            name = info.filename
            posix = PurePosixPath(name)
            require(name and not name.startswith("/"), f"Absolute ZIP member: {name}")
            require("\\" not in name and ".." not in posix.parts, f"Unsafe ZIP member: {name}")
            rows.append(
                {
                    "member_sequence": sequence,
                    "member_name": name,
                    "member_is_dir": info.is_dir(),
                    "member_size": info.file_size,
                    "member_compressed_size": info.compress_size,
                    "member_crc32": f"{info.CRC:08x}",
                    "zip_utf8_filename_flag": bool(info.flag_bits & 0x800),
                }
            )
    return rows


def validate_official_recheck(lock: dict) -> None:
    path = ROOT / lock["official_recheck_manifest"]
    require(path.is_file(), f"Missing official recheck manifest: {path}")
    manifest = load_yaml(path)
    require(manifest.get("status") == "PASS", "Official recheck did not pass")
    pages = manifest.get("pages", [])
    require(len(pages) >= 9, "Official page hash manifest is incomplete")
    require(all(page.get("status") == 200 for page in pages), "Official recheck contains non-200 response")
    assertions = manifest.get("assertions", {})
    require(assertions.get("economic_census_table") == "T001163", "Economic table pin missing")
    require(assertions.get("population_census_table") == "T001141", "Population table pin missing")
    require(assertions.get("population_census_excluded_lookalike_table") == "T001192", "Lookalike table guard missing")
    require(assertions.get("l01_correction_date_floor") == "2026-04-24", "L01 correction floor missing")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", type=Path, default=ROOT / "data/reference/PHASE1_ACQUISITION_SCOPE.yml")
    parser.add_argument("--lock", type=Path, default=ROOT / "data/manifests/source_lock.phase1.yml")
    args = parser.parse_args()
    scope_path = args.scope if args.scope.is_absolute() else ROOT / args.scope
    lock_path = args.lock if args.lock.is_absolute() else ROOT / args.lock
    scope = load_yaml(scope_path)
    lock = load_yaml(lock_path)
    validate_official_recheck(lock)
    expected = expand_artifacts(scope)
    locked = {item["artifact_id"]: item for item in lock.get("artifacts", [])}
    require(set(locked) == {item["artifact_id"] for item in expected}, "Lock artifact set differs from scope")
    require(lock.get("artifact_count") == len(expected), "Lock artifact_count mismatch")

    member_path = ROOT / lock["archive_member_index"]
    require(member_path.is_file(), f"Missing archive member index: {member_path}")
    member_table = pq.read_table(member_path).to_pylist()
    member_by_artifact: dict[str, list[dict[str, object]]] = {}
    for row in member_table:
        member_by_artifact.setdefault(row["artifact_id"], []).append(row)
    require(lock.get("member_count") == len(member_table), "Lock member_count mismatch")

    expected_archive_paths: set[str] = set()
    expected_header_paths: set[str] = set()
    for spec in expected:
        artifact_id = spec["artifact_id"]
        row = locked[artifact_id]
        require(row["source_id"] == spec["source_id"], f"source_id drift: {artifact_id}")
        require(row["source_release_id"] == spec["source_release_id"], f"release drift: {artifact_id}")
        require(row["url"] == spec["url"], f"URL drift: {artifact_id}")
        for key in ("url", "final_url"):
            host = urlparse(row[key]).hostname
            require(host in ALLOWED_HOSTS, f"Unapproved {key} host: {row[key]}")
        local = safe_raw_path(row["local_path"])
        headers_path = safe_raw_path(row["headers_path"])
        expected_archive_paths.add(row["local_path"])
        expected_header_paths.add(row["headers_path"])
        require(local.is_file(), f"Missing locked archive: {local}")
        require(headers_path.is_file(), f"Missing locked headers: {headers_path}")
        require(local.stat().st_size == row["byte_size"], f"Byte size drift: {artifact_id}")
        require(sha256(local) == row["sha256"], f"SHA-256 drift: {artifact_id}")
        headers = parse_headers(headers_path)
        require(headers["final_status"] == 200, f"Non-200 response: {artifact_id}")
        expected_length = headers.get("content_length")
        require(expected_length is None or expected_length == local.stat().st_size, f"Content-Length drift: {artifact_id}")
        actual_members = verify_zip(local)
        locked_members = member_by_artifact.get(artifact_id, [])
        require(len(actual_members) == len(locked_members), f"Member count drift: {artifact_id}")
        for actual, locked_member in zip(actual_members, locked_members):
            for key in actual:
                require(actual[key] == locked_member[key], f"Member metadata drift {artifact_id}: {key}")
        require(row["zip_member_count"] == len(actual_members), f"Archive member count field drift: {artifact_id}")

        # Every textual member must have a detected encoding.  e-Stat tables
        # are CP932 in the delivered bytes; this catches an accidental UTF-8
        # assumption before any numeric parsing.
        for member in locked_members:
            if member["payload_kind"] in TEXT_KINDS:
                require(member["encoding"], f"Unknown text encoding: {artifact_id}/{member['member_name']}")
        if spec.get("table_id") in {"T001163", "T001141"}:
            for member in locked_members:
                if member["payload_kind"] == "text":
                    require(member["encoding"] in {"cp932", "shift_jis"}, f"Unexpected e-Stat encoding: {artifact_id}")
        if spec.get("table_id") == "T001141":
            require(spec.get("table_id") != "T001192", "Population input accidentally bound to T001192")
        if artifact_id == "l01-26-13-gml":
            require(row.get("correction_date_floor") == "2026-04-24", "L01 Tokyo correction floor missing")

    archive_root = ROOT / "data/raw/phase1/archives"
    header_root = ROOT / "data/raw/phase1/http"
    actual_archives = {path.relative_to(ROOT).as_posix() for path in archive_root.rglob("*.zip")}
    actual_headers = {path.relative_to(ROOT).as_posix() for path in header_root.rglob("*.headers")}
    require(actual_archives == expected_archive_paths, f"Unregistered archive files: {sorted(actual_archives ^ expected_archive_paths)}")
    require(actual_headers == expected_header_paths, f"Unregistered header files: {sorted(actual_headers ^ expected_header_paths)}")
    require(not list(archive_root.rglob("*.part")), "Partial archive remains under archive root")
    require(not list(header_root.rglob("*.part")), "Partial header remains under header root")
    require(lock.get("raw_archives_in_git") is False, "Raw archive policy changed")
    require(lock.get("gate") == "G1", "Lock is not a G1 lock")
    print(f"PASS Phase 1 source lock: {len(expected)} archives, {len(member_table)} members")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
