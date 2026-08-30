#!/usr/bin/env python3
"""Build the Phase 1 source lock and archive-member index.

The lock is deliberately generated from the downloaded bytes, not from an
expected filename or an HTTP header alone.  Raw archives remain outside Git;
the YAML/Parquet outputs are the reproducible provenance record.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from typing import Any, Iterable
from zipfile import ZipFile

import pyarrow as pa
import pyarrow.parquet as pq
import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCOPE = ROOT / "data/reference/PHASE1_ACQUISITION_SCOPE.yml"
DEFAULT_LOCK = ROOT / "data/manifests/source_lock.phase1.yml"
DEFAULT_MEMBERS = ROOT / "data/manifests/archive_members.phase1.parquet"
DEFAULT_LOG = ROOT / "data/manifests/acquisition_log.phase1.jsonl"
TEXT_SUFFIXES = {".csv", ".geojson", ".json", ".prj", ".txt", ".xml", ".xsd"}
BINARY_SUFFIXES = {".dbf", ".shp", ".shx"}


def utc_iso(timestamp: float | None = None) -> str:
    value = datetime.now(timezone.utc) if timestamp is None else datetime.fromtimestamp(timestamp, timezone.utc)
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected mapping in {path}")
    return value


def expand_artifacts(scope: dict[str, Any]) -> list[dict[str, Any]]:
    expanded: list[dict[str, Any]] = []
    for spec in scope.get("artifacts", []):
        codes = spec.get("prefecture_codes")
        if codes is None:
            item = dict(spec)
            item["artifact_id"] = str(spec["artifact_id"])
            item["url"] = str(spec["url"])
            item["local_path"] = str(spec["local_path"])
            item["headers_path"] = str(spec["headers_path"])
            expanded.append(item)
            continue
        for code in codes:
            code = str(code).zfill(2)
            item = dict(spec)
            item["artifact_id"] = f"{spec['artifact_id']}-{code}"
            item["prefecture_code"] = code
            item["url"] = str(spec["url_template"]).format(prefecture_code=code)
            item["local_path"] = str(spec["local_path_template"]).format(prefecture_code=code)
            item["headers_path"] = str(spec["headers_path_template"]).format(prefecture_code=code)
            expanded.append(item)
    if not expanded:
        raise ValueError("No artifacts declared in the Phase 1 scope")
    ids = [item["artifact_id"] for item in expanded]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate artifact_id in Phase 1 scope")
    return expanded


def assert_raw_path(path: Path) -> None:
    raw_root = (ROOT / "data/raw/phase1").resolve()
    resolved = path.resolve()
    if raw_root not in resolved.parents:
        raise ValueError(f"Raw path escapes data/raw/phase1: {path}")


def parse_headers(path: Path) -> dict[str, Any]:
    """Parse curl's possibly multi-response dump-header into final response metadata."""

    lines = path.read_text(encoding="iso-8859-1").splitlines()
    responses: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in lines:
        if line.startswith("HTTP/"):
            if current is not None:
                responses.append(current)
            parts = line.split(None, 2)
            current = {
                "status_line": line,
                "protocol": parts[0] if parts else None,
                "status": int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None,
                "headers": {},
            }
            continue
        if current is None or not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        # Repeated response headers are retained as a list instead of silently lost.
        existing = current["headers"].get(key)
        if existing is None:
            current["headers"][key] = value
        elif isinstance(existing, list):
            existing.append(value)
        else:
            current["headers"][key] = [existing, value]
    if current is not None:
        responses.append(current)
    if not responses:
        raise ValueError(f"No HTTP response found in {path}")
    final = responses[-1]
    headers = final["headers"]
    content_length = headers.get("content-length")
    try:
        content_length_int = int(content_length) if isinstance(content_length, str) else None
    except ValueError:
        content_length_int = None
    return {
        "response_chain": [
            {"status_line": item["status_line"], "status": item["status"], "protocol": item["protocol"]}
            for item in responses
        ],
        "final_status": final["status"],
        "final_headers": headers,
        "content_length": content_length_int,
        "content_type": headers.get("content-type"),
        "content_disposition": headers.get("content-disposition"),
        "etag": headers.get("etag"),
        "last_modified": headers.get("last-modified"),
        "date": headers.get("date"),
        "final_url_from_header": headers.get("location"),
    }


def safe_member_name(name: str) -> None:
    path = PurePosixPath(name)
    if not name or name.startswith("/") or "\\" in name or any(part == ".." for part in path.parts):
        raise ValueError(f"Unsafe ZIP member path: {name!r}")


def declared_encoding(sample: bytes) -> str | None:
    match = re.search(rb"encoding\s*=\s*['\"]([^'\"]+)['\"]", sample[:4096], flags=re.IGNORECASE)
    if match:
        return match.group(1).decode("ascii", errors="replace").lower()
    return None


def probe_encoding(info, payload: bytes) -> dict[str, Any]:
    suffix = Path(info.filename).suffix.lower()
    if suffix in BINARY_SUFFIXES:
        return {
            "payload_kind": "binary",
            "encoding": None,
            "encoding_candidates": [],
            "declared_encoding": None,
            "probe_bytes": len(payload),
        }
    if suffix not in TEXT_SUFFIXES:
        return {
            "payload_kind": "opaque",
            "encoding": None,
            "encoding_candidates": [],
            "declared_encoding": None,
            "probe_bytes": len(payload),
        }
    declared = declared_encoding(payload)
    candidates: list[str] = []
    for encoding in ("utf-8-sig", "cp932", "shift_jis", "utf-16"):
        try:
            payload.decode(encoding)
        except UnicodeDecodeError:
            continue
        candidates.append(encoding)
    chosen = candidates[0] if candidates else None
    return {
        "payload_kind": "text",
        "encoding": chosen,
        "encoding_candidates": candidates,
        "declared_encoding": declared,
        "probe_bytes": len(payload),
    }


def archive_metadata(path: Path, artifact_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    member_rows: list[dict[str, Any]] = []
    with ZipFile(path) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise ValueError(f"CRC failure in {path}: {bad}")
        for sequence, info in enumerate(archive.infolist(), start=1):
            safe_member_name(info.filename)
            sample = b"" if info.is_dir() else archive.read(info)[:1024 * 1024]
            encoding = probe_encoding(info, sample)
            member_rows.append(
                {
                    "artifact_id": artifact_id,
                    "archive_path": path.relative_to(ROOT).as_posix(),
                    "member_sequence": sequence,
                    "member_name": info.filename,
                    "member_is_dir": info.is_dir(),
                    "member_size": info.file_size,
                    "member_compressed_size": info.compress_size,
                    "member_crc32": f"{info.CRC:08x}",
                    "zip_utf8_filename_flag": bool(info.flag_bits & 0x800),
                    **encoding,
                }
            )
    return {
        "archive_tested": True,
        "zip_member_count": len(member_rows),
        "zip_member_file_count": sum(not row["member_is_dir"] for row in member_rows),
    }, member_rows


def decompressor_versions() -> dict[str, str]:
    versions: dict[str, str] = {"python": sys.version.split()[0], "pyarrow": pa.__version__}
    for command, label in ((["unzip", "-v"], "unzip"), (['curl', '--version'], "curl")):
        try:
            output = subprocess.run(command, check=True, capture_output=True, text=True).stdout.splitlines()
        except (OSError, subprocess.CalledProcessError):
            continue
        if output:
            versions[label] = output[0].strip()
    return versions


def expand_and_measure(scope: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    artifacts: list[dict[str, Any]] = []
    members: list[dict[str, Any]] = []
    for spec in expand_artifacts(scope):
        local_path = ROOT / spec["local_path"]
        headers_path = ROOT / spec["headers_path"]
        assert_raw_path(local_path)
        assert_raw_path(headers_path)
        if not local_path.is_file():
            raise FileNotFoundError(local_path)
        if not headers_path.is_file():
            raise FileNotFoundError(headers_path)
        if spec.get("expected_format") == "zip":
            archive_summary, rows = archive_metadata(local_path, spec["artifact_id"])
        else:
            raise ValueError(f"Unsupported format for {spec['artifact_id']}")
        header_summary = parse_headers(headers_path)
        expected_length = header_summary["content_length"]
        byte_size = local_path.stat().st_size
        if expected_length is not None and expected_length != byte_size:
            raise ValueError(
                f"Content-Length mismatch for {spec['artifact_id']}: expected {expected_length}, got {byte_size}"
            )
        text_fields = {
            "artifact_id": spec["artifact_id"],
            "source_id": spec["source_id"],
            "source_release_id": spec["source_release_id"],
            "kind": spec.get("kind"),
            "table_id": spec.get("table_id"),
            "aggregate_unit": spec.get("aggregate_unit"),
            "mesh_level": spec.get("mesh_level"),
            "nominal_resolution_m": spec.get("nominal_resolution_m"),
            "datum": spec.get("datum"),
            "prefecture_code": spec.get("prefecture_code"),
            "url": spec["url"],
            "final_url": spec["url"],
            "local_path": local_path.relative_to(ROOT).as_posix(),
            "headers_path": headers_path.relative_to(ROOT).as_posix(),
            "retrieved_at": utc_iso(local_path.stat().st_mtime),
            "byte_size": byte_size,
            "sha256": sha256(local_path),
            "http": header_summary,
            "encoding_expectation": spec.get("expected_encoding"),
            "reference_date_or_period": spec.get("reference_date_or_period"),
            "publication_date_or_period": spec.get("publication_date_or_period"),
            "distribution_date": spec.get("distribution_date"),
            "correction_date_floor": spec.get("correction_date_floor"),
            "correction_log_url": spec.get("correction_log_url"),
            "terms_url": spec.get("terms_url"),
            **archive_summary,
        }
        artifacts.append(text_fields)
        members.extend(rows)
    return artifacts, members


def write_outputs(scope: dict[str, Any], artifacts: list[dict[str, Any]], members: list[dict[str, Any]], lock_path: Path, members_path: Path, log_path: Path) -> None:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    members_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    generated_at = utc_iso()
    lock = {
        "lock_version": "0.1.0",
        "project_id": scope["project_id"],
        "phase": scope["phase"],
        "gate": scope["gate"],
        "locked_at": generated_at,
        "generated_by": "scripts/build_source_lock.py",
        "tool_versions": decompressor_versions(),
        "official_recheck": scope.get("official_recheck", {}),
        "official_recheck_manifest": "data/manifests/official_recheck.phase1.yml",
        "scope_file": str((ROOT / "data/reference/PHASE1_ACQUISITION_SCOPE.yml").relative_to(ROOT)),
        "raw_root": "data/raw/phase1",
        "raw_archives_in_git": False,
        "archive_member_index": str(members_path.relative_to(ROOT)),
        "acquisition_log": str(log_path.relative_to(ROOT)),
        "artifact_count": len(artifacts),
        "member_count": len(members),
        "artifacts": artifacts,
    }
    with lock_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(lock, handle, allow_unicode=True, sort_keys=False)

    # A typed Parquet index is required by the Phase 1 plan.  Keep nullable
    # fields as strings/integers so a later ETL can join without guessing.
    columns = [
        "artifact_id", "archive_path", "member_sequence", "member_name", "member_is_dir",
        "member_size", "member_compressed_size", "member_crc32", "zip_utf8_filename_flag",
        "payload_kind", "encoding", "encoding_candidates", "declared_encoding", "probe_bytes",
    ]
    normalized = []
    for row in members:
        copy = dict(row)
        copy["encoding_candidates"] = json.dumps(copy["encoding_candidates"], ensure_ascii=False)
        normalized.append([copy.get(column) for column in columns])
    arrays = {column: [row[index] for row in normalized] for index, column in enumerate(columns)}
    table = pa.table(arrays)
    pq.write_table(table, members_path, compression="zstd", version="2.6")

    with log_path.open("w", encoding="utf-8") as handle:
        for artifact in artifacts:
            event = {
                "artifact_id": artifact["artifact_id"],
                "source_release_id": artifact["source_release_id"],
                "url": artifact["url"],
                "final_url": artifact["final_url"],
                "retrieved_at": artifact["retrieved_at"],
                "http_status": artifact["http"]["final_status"],
                "byte_size": artifact["byte_size"],
                "sha256": artifact["sha256"],
                "archive_tested": artifact["archive_tested"],
                "zip_member_count": artifact["zip_member_count"],
                "result": "locked",
            }
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", type=Path, default=DEFAULT_SCOPE)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--members", type=Path, default=DEFAULT_MEMBERS)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    args = parser.parse_args()
    scope = load_yaml(args.scope if args.scope.is_absolute() else ROOT / args.scope)
    artifacts, members = expand_and_measure(scope)
    write_outputs(
        scope,
        artifacts,
        members,
        args.lock if args.lock.is_absolute() else ROOT / args.lock,
        args.members if args.members.is_absolute() else ROOT / args.members,
        args.log if args.log.is_absolute() else ROOT / args.log,
    )
    print(f"LOCKED {len(artifacts)} artifacts; {len(members)} archive members")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
