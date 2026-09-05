#!/usr/bin/env python3
"""Acquire the fixed Phase 1 source scope with atomic, immutable writes.

The command intentionally never extracts or transforms a source archive.  A
successful download is first written beside the destination, checked as a ZIP,
and then atomically renamed.  Existing final files are skipped unless
``--force`` is explicitly supplied.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from urllib.parse import urlparse
from zipfile import ZipFile

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_source_lock import ROOT, expand_artifacts, load_yaml, parse_headers, sha256


ALLOWED_HOSTS = {"nlftp.mlit.go.jp", "www.e-stat.go.jp"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def assert_raw_path(path: Path) -> None:
    root = (ROOT / "data/raw/phase1").resolve()
    if root not in path.resolve().parents:
        raise ValueError(f"Path outside data/raw/phase1: {path}")


def verify_zip(path: Path) -> int:
    with ZipFile(path) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f"CRC failure in {path}: {bad}")
        for info in archive.infolist():
            name = info.filename
            if name.startswith("/") or "\\" in name or ".." in Path(name).parts:
                raise ValueError(f"Unsafe ZIP member path: {name!r}")
        return len(archive.infolist())


def acquire_one(spec: dict, force: bool) -> dict[str, object]:
    local = ROOT / spec["local_path"]
    headers = ROOT / spec["headers_path"]
    assert_raw_path(local)
    assert_raw_path(headers)
    local.parent.mkdir(parents=True, exist_ok=True)
    headers.parent.mkdir(parents=True, exist_ok=True)
    if local.exists() and headers.exists() and not force:
        return {"artifact_id": spec["artifact_id"], "result": "skipped_existing", "local_path": str(local.relative_to(ROOT))}

    parsed = urlparse(spec["url"])
    if parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError(f"Unapproved download host: {spec['url']}")
    # Keep interrupted download remnants outside ``archives``.  The lock
    # validator treats every ZIP below that directory as an asserted raw
    # artifact, so staging there turns an interrupted transfer into a false
    # source-lock mismatch.  Quarantine is intentionally excluded from the
    # asserted input set and can preserve failure evidence for inspection.
    staging_root = ROOT / "data/raw/phase1/quarantine/staging"
    assert_raw_path(staging_root)
    staging_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="phase1-acquire-", dir=str(staging_root)) as temp_dir:
        temp_root = Path(temp_dir)
        part = temp_root / local.name
        header_part = temp_root / headers.name
        command = [
            "curl", "--fail", "--location", "--retry", "4", "--retry-all-errors", "--retry-delay", "2",
            "--connect-timeout", "30", "--max-time", "1200", "--dump-header", str(header_part),
            "--output", str(part), "--write-out", "%{url_effective}\\t%{http_code}", spec["url"],
        ]
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        url_effective, status = (result.stdout.strip().split("\t", 1) + [None, None])[:2]
        header_summary = parse_headers(header_part)
        if header_summary["final_status"] != 200:
            raise ValueError(f"Unexpected HTTP status for {spec['artifact_id']}: {header_summary['final_status']}")
        expected_length = header_summary.get("content_length")
        actual_length = part.stat().st_size
        if expected_length is not None and expected_length != actual_length:
            raise ValueError(f"Content-Length mismatch for {spec['artifact_id']}: {expected_length} != {actual_length}")
        member_count = verify_zip(part)
        os.replace(part, local)
        os.replace(header_part, headers)
    return {
        "artifact_id": spec["artifact_id"],
        "result": "acquired",
        "url": spec["url"],
        "final_url": url_effective or spec["url"],
        "http_status": int(status) if status and status.isdigit() else header_summary["final_status"],
        "retrieved_at": utc_now(),
        "local_path": str(local.relative_to(ROOT)),
        "byte_size": local.stat().st_size,
        "sha256": sha256(local),
        "zip_member_count": member_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", type=Path, default=ROOT / "data/reference/PHASE1_ACQUISITION_SCOPE.yml")
    parser.add_argument("--force", action="store_true", help="Replace existing final files; use only for an explicit new lock")
    parser.add_argument("--event-log", type=Path, default=ROOT / "data/raw/phase1/acquisition_events.jsonl")
    args = parser.parse_args()
    scope_path = args.scope if args.scope.is_absolute() else ROOT / args.scope
    scope = load_yaml(scope_path)
    events = []
    for spec in expand_artifacts(scope):
        event = acquire_one(spec, args.force)
        events.append(event)
        print(f"{event['result'].upper()} {event['artifact_id']}")
    log_path = args.event_log if args.event_log.is_absolute() else ROOT / args.event_log
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"WROTE {log_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
