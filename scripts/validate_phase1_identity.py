#!/usr/bin/env python3
"""Validate the review-only Phase 1 G2 identity candidate artifacts."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pyarrow.parquet as pq
import yaml


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/manifests/identity.phase1.yml"
REGISTRY = ROOT / "data/reference/PHASE1_IDENTITY_REGISTRY.yml"
RULES = ROOT / "data/reference/PHASE1_IDENTITY_RULES.yml"
LOCK = ROOT / "data/manifests/source_lock.phase1.yml"
N02_ARCHIVE = ROOT / "data/raw/phase1/archives/N02-25_GML.zip"

EXPECTED = {
    "stations": ROOT / "data/derived/stations.parquet",
    "station_groups": ROOT / "data/derived/station_groups.parquet",
    "hubs": ROOT / "data/derived/hubs.parquet",
    "hub_station_group_links": ROOT / "data/derived/hub_station_group_links.parquet",
    "lines": ROOT / "data/derived/lines.parquet",
    "station_line_crosswalk": ROOT / "data/derived/station_line_crosswalk.parquet",
    "station_group_members": ROOT / "data/derived/station_group_members.parquet",
    "entity_alias": ROOT / "data/derived/entity_alias.parquet",
    "identity_review_queue": ROOT / "data/qa/identity_review_queue.parquet",
}


def fail(message: str) -> None:
    raise SystemExit(f"FAIL {message}")


def read_rows(path: Path) -> list[dict]:
    try:
        return pq.read_table(path).to_pylist()
    except Exception as exc:  # pragma: no cover - diagnostic wrapper
        fail(f"cannot read {path.relative_to(ROOT)}: {exc}")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    for path in [MANIFEST, REGISTRY, RULES, LOCK, N02_ARCHIVE, *EXPECTED.values()]:
        if not path.exists():
            fail(f"missing {path.relative_to(ROOT)}")
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    rules = yaml.safe_load(RULES.read_text(encoding="utf-8"))
    lock = yaml.safe_load(LOCK.read_text(encoding="utf-8"))
    if manifest.get("status") != "CANDIDATE_REVIEW" or manifest.get("gate") != "G2":
        fail("manifest must remain G2 CANDIDATE_REVIEW")
    if len(rules.get("corridors", {})) != 8:
        fail("identity rules do not contain exactly 8 corridors")
    maps = registry.get("maps", {})
    for kind in ("line", "station", "station_group", "hub", "alias", "review"):
        if not isinstance(maps.get(kind), dict):
            fail(f"registry map missing: {kind}")
    prefix = {"line": "lin_", "station": "sta_", "station_group": "stg_", "hub": "hub_", "alias": "als_", "review": "idr_"}
    opaque = re.compile(r"^(?:lin|sta|stg|hub|als|idr)_[0-9a-f]{32}$")
    for kind, entries in maps.items():
        for key, value in entries.items():
            if not opaque.match(str(value)) or not str(value).startswith(prefix.get(kind, "")):
                fail(f"non-opaque {kind} ID in registry: {value}")
            if str(value) in key:
                fail(f"source-derived key leaked into canonical ID: {value}")

    rows = {name: read_rows(path) for name, path in EXPECTED.items()}
    counts = manifest.get("counts", {})
    expected_count_key = {
        "stations": "stations", "station_groups": "station_groups", "hubs": "hubs", "lines": "lines",
        "station_line_crosswalk": "crosswalk_rows", "identity_review_queue": "review_queue",
    }
    for name, count_key in expected_count_key.items():
        if len(rows[name]) != counts.get(count_key):
            fail(f"manifest count mismatch for {name}: {len(rows[name])} != {counts.get(count_key)}")
    for name, path in EXPECTED.items():
        digest = sha256(path)
        recorded = manifest.get("outputs", {}).get(name, {}).get("sha256")
        if digest != recorded:
            fail(f"output hash mismatch for {name}")

    station_ids = {row["station_id"] for row in rows["stations"]}
    group_ids = {row["station_group_id"] for row in rows["station_groups"]}
    hub_ids = {row["hub_id"] for row in rows["hubs"]}
    line_ids = {row["line_id"] for row in rows["lines"]}
    review_ids = {row["review_id"] for row in rows["identity_review_queue"]}
    if len(station_ids) != len(rows["stations"]) or len(group_ids) != len(rows["station_groups"]):
        fail("station or station_group IDs are not unique")
    if len(hub_ids) != len(rows["hubs"]) or len(line_ids) != len(rows["lines"]):
        fail("hub or line IDs are not unique")
    if len(review_ids) != len(rows["identity_review_queue"]):
        fail("review IDs are not unique")
    for collection, kind in ((station_ids, "station"), (group_ids, "station_group"), (hub_ids, "hub"), (line_ids, "line")):
        if any(not value.startswith(prefix[kind]) or not opaque.match(value) for value in collection):
            fail(f"{kind} output contains non-opaque ID")

    # Source identifiers are aliases only; they may not occupy canonical ID columns.
    source_keys = {row["n02_station_key"] for row in rows["stations"]}
    if station_ids & source_keys:
        fail("N02 station key was used as station_id")
    for row in rows["stations"]:
        if row["n02_source_release_id"] != "N02-25" or not row["n02_station_key"]:
            fail("station provenance is incomplete")
    for row in rows["entity_alias"]:
        if row["entity_id"] not in station_ids | group_ids | hub_ids | line_ids:
            fail("alias points to unknown entity")
        if row["source_release_id"] != "N02-25":
            fail("alias source release is not N02-25")
    alias_keys = [(r["source_release_id"], r["source_namespace"], r["source_key"], r["entity_type"]) for r in rows["entity_alias"]]
    if len(alias_keys) != len(set(alias_keys)):
        fail("entity_alias source uniqueness violated")

    # Every selected source station membership resolves to an existing station and line;
    # ambiguity is represented in the queue, never as a forced crosswalk row.
    memberships = [(r["station_id"], r["line_id"], r["membership_valid_from"]) for r in rows["station_line_crosswalk"]]
    if len(memberships) != len(set(memberships)):
        fail("station-line crosswalk primary key duplicated")
    by_line: dict[str, list[int]] = {}
    for row in rows["station_line_crosswalk"]:
        if row["station_id"] not in station_ids or row["station_group_id"] not in group_ids or row["line_id"] not in line_ids:
            fail("crosswalk foreign key unresolved")
        if row["hub_id"] is not None and row["hub_id"] not in hub_ids:
            fail("crosswalk hub foreign key unresolved")
        if row["identity_review_id"] is not None and row["identity_review_id"] not in review_ids:
            fail("crosswalk review key unresolved")
        if row["n02_source_release_id"] != "N02-25" or row["n02_station_key"] in station_ids:
            fail("crosswalk source provenance/canonical separation violated")
        if row["identity_resolution_status"].startswith("unresolved"):
            fail("unresolved identity was forced into crosswalk")
        by_line.setdefault(row["line_id"], []).append(row["sequence_index"])
    if set(by_line) != line_ids:
        fail("one or more canonical pilot lines have no crosswalk rows")
    for line_id, sequence in by_line.items():
        if sequence != sorted(sequence) or len(sequence) != len(set(sequence)):
            fail(f"sequence is not strictly ordered for {line_id}")
    if len({r["pilot_corridor_id"] for r in rows["lines"]}) != 8:
        fail("line output does not resolve all pilot corridors")

    for row in rows["hubs"]:
        if row["review_status"] != "candidate" or row["transfer_basis"] != "manual":
            fail("hub was auto-confirmed")
    for row in rows["hub_station_group_links"]:
        if row["hub_id"] not in hub_ids or row["station_group_id"] not in group_ids:
            fail("hub link foreign key unresolved")
        if row["is_manual"] != 0:
            fail("hub link marked manual before G2 adjudication")
    allowed_issues = {"no_match", "ambiguous_match", "collision", "split_candidate", "merge_candidate"}
    for row in rows["identity_review_queue"]:
        if row["issue_type"] not in allowed_issues or row["status"] not in {"open", "resolved", "wont_fix"}:
            fail("invalid identity review status/type")
    if not any(row["status"] == "open" for row in rows["identity_review_queue"]):
        fail("G2 candidate run must retain an open review queue")

    n02_artifacts = [a for a in lock.get("artifacts", []) if a.get("artifact_id") == "n02-25-gml"]
    if len(n02_artifacts) != 1 or n02_artifacts[0].get("source_release_id") != "N02-25":
        fail("G1 source lock has no N02-25 artifact")
    if sha256(N02_ARCHIVE) != n02_artifacts[0].get("sha256"):
        fail("N02 archive does not match G1 source lock")
    print(
        "PASS Phase 1 G2 identity candidates: "
        f"{len(rows['stations'])} stations, {len(rows['station_line_crosswalk'])} crosswalk rows, "
        f"{sum(row['status'] == 'open' for row in rows['identity_review_queue'])} open reviews"
    )


if __name__ == "__main__":
    main()
