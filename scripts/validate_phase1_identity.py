#!/usr/bin/env python3
"""Validate the adjudicated Phase 1 G2 identity and exact-segment artifacts."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

import pyarrow.parquet as pq
import yaml


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/manifests/identity.phase1.yml"
REGISTRY = ROOT / "data/reference/PHASE1_IDENTITY_REGISTRY.yml"
RULES = ROOT / "data/reference/PHASE1_IDENTITY_RULES.yml"
ADJUDICATION = ROOT / "data/reference/PHASE1_G2_ADJUDICATIONS.yml"
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


def sha256_json(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def main() -> None:
    for path in [MANIFEST, REGISTRY, RULES, ADJUDICATION, LOCK, N02_ARCHIVE, *EXPECTED.values()]:
        if not path.exists():
            fail(f"missing {path.relative_to(ROOT)}")

    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    rules = yaml.safe_load(RULES.read_text(encoding="utf-8"))
    adjudication = yaml.safe_load(ADJUDICATION.read_text(encoding="utf-8"))
    lock = yaml.safe_load(LOCK.read_text(encoding="utf-8"))

    if manifest.get("status") != "PASS" or manifest.get("gate") != "G2":
        fail("manifest must record G2 PASS")
    if rules.get("status") != "adjudicated" or adjudication.get("status") != "accepted":
        fail("rules/adjudication have not been accepted")
    if manifest.get("rules_sha256") != sha256(RULES):
        fail("manifest identity-rule hash mismatch")
    if manifest.get("adjudication_sha256") != sha256(ADJUDICATION):
        fail("manifest adjudication hash mismatch")

    corridors = rules.get("corridors", {})
    decisions = adjudication.get("review_decisions", [])
    segment_decisions = {
        row["corridor_id"]: row for row in adjudication.get("service_segments", [])
    }
    acceptance = adjudication.get("acceptance", {})
    if len(corridors) != 8 or set(segment_decisions) != set(corridors):
        fail("adjudication does not lock exactly the eight pilot corridors")
    if len(decisions) != acceptance.get("expected_preexisting_open_reviews"):
        fail("manual review decision count does not match the accepted contract")
    if len({row["source_key"] for row in decisions}) != len(decisions):
        fail("manual review source key duplicated")
    for decision in decisions:
        if decision.get("decision") not in {"confirm_hub", "reject_hub", "resolve_duplicate"}:
            fail(f"unknown hub decision: {decision.get('source_key')}")
        evidence = decision.get("evidence", [])
        if not evidence or any(not str(item.get("url", "")).startswith("https://") for item in evidence):
            fail(f"manual decision lacks official HTTPS evidence: {decision.get('source_key')}")

    maps = registry.get("maps", {})
    prefix = {
        "line": "lin_", "station": "sta_", "station_group": "stg_",
        "hub": "hub_", "alias": "als_", "review": "idr_",
    }
    opaque = re.compile(r"^(?:lin|sta|stg|hub|als|idr)_[0-9a-f]{32}$")
    for kind in prefix:
        if not isinstance(maps.get(kind), dict):
            fail(f"registry map missing: {kind}")
        for key, value in maps[kind].items():
            if not opaque.match(str(value)) or not str(value).startswith(prefix[kind]):
                fail(f"non-opaque {kind} ID in registry: {value}")
            if str(value) in key:
                fail(f"source-derived key leaked into canonical ID: {value}")

    rows = {name: read_rows(path) for name, path in EXPECTED.items()}
    counts = manifest.get("counts", {})
    expected_count_key = {
        "stations": "stations", "station_groups": "station_groups", "hubs": "hubs",
        "lines": "lines", "station_line_crosswalk": "crosswalk_rows",
        "identity_review_queue": "review_queue",
    }
    for name, count_key in expected_count_key.items():
        if len(rows[name]) != counts.get(count_key):
            fail(f"manifest count mismatch for {name}: {len(rows[name])} != {counts.get(count_key)}")
    for name, path in EXPECTED.items():
        if sha256(path) != manifest.get("outputs", {}).get(name, {}).get("sha256"):
            fail(f"output hash mismatch for {name}")

    station_ids = {row["station_id"] for row in rows["stations"]}
    group_ids = {row["station_group_id"] for row in rows["station_groups"]}
    hub_ids = {row["hub_id"] for row in rows["hubs"]}
    line_ids = {row["line_id"] for row in rows["lines"]}
    review_ids = {row["review_id"] for row in rows["identity_review_queue"]}
    unique_sets = {
        "station": (station_ids, rows["stations"]),
        "station_group": (group_ids, rows["station_groups"]),
        "hub": (hub_ids, rows["hubs"]),
        "line": (line_ids, rows["lines"]),
        "review": (review_ids, rows["identity_review_queue"]),
    }
    for kind, (identifiers, source_rows) in unique_sets.items():
        if len(identifiers) != len(source_rows):
            fail(f"{kind} IDs are not unique")
        if any(not value.startswith(prefix[kind]) or not opaque.match(value) for value in identifiers):
            fail(f"{kind} output contains non-opaque ID")

    source_keys = {row["n02_station_key"] for row in rows["stations"]}
    if station_ids & source_keys:
        fail("N02 station key was used as station_id")
    for row in rows["stations"]:
        if row["n02_source_release_id"] != "N02-25" or not row["n02_station_key"]:
            fail("station provenance is incomplete")
        if "candidate" in row["identity_resolution_status"] or "unresolved" in row["identity_resolution_status"]:
            fail("station identity remained candidate/unresolved after G2")
    if any(row["review_status"] != "confirmed" for row in rows["station_groups"]):
        fail("station group remained unconfirmed after G2")
    if any(row["review_status"] != "confirmed" for row in rows["station_group_members"]):
        fail("station-group membership remained unconfirmed after G2")

    all_entity_ids = station_ids | group_ids | hub_ids | line_ids
    alias_keys = []
    for row in rows["entity_alias"]:
        expected_release = (
            adjudication["adjudication_release_id"] if row["entity_type"] == "hub" else "N02-25"
        )
        if row["entity_id"] not in all_entity_ids or row["source_release_id"] != expected_release:
            fail("alias points to unknown entity or wrong source/adjudication release")
        if row["review_status"] != "confirmed":
            fail("entity alias remained unconfirmed after G2")
        alias_keys.append(
            (row["source_release_id"], row["source_namespace"], row["source_key"], row["entity_type"])
        )
    if len(alias_keys) != len(set(alias_keys)):
        fail("entity_alias source uniqueness violated")

    stations_by_id = {row["station_id"]: row for row in rows["stations"]}
    crosswalk_by_line: dict[str, list[dict]] = defaultdict(list)
    memberships = []
    for row in rows["station_line_crosswalk"]:
        memberships.append((row["station_id"], row["line_id"], row["membership_valid_from"]))
        if row["station_id"] not in station_ids or row["station_group_id"] not in group_ids or row["line_id"] not in line_ids:
            fail("crosswalk foreign key unresolved")
        if row["hub_id"] is not None and row["hub_id"] not in hub_ids:
            fail("crosswalk hub foreign key unresolved")
        if row["identity_review_id"] is not None and row["identity_review_id"] not in review_ids:
            fail("crosswalk review key unresolved")
        if row["n02_source_release_id"] != "N02-25" or row["n02_station_key"] in station_ids:
            fail("crosswalk source provenance/canonical separation violated")
        if row["segment_inclusion_status"] != "primary_confirmed":
            fail("crosswalk contains an unlocked service membership")
        if row["identity_resolution_status"].startswith("unresolved"):
            fail("unresolved identity was forced into crosswalk")
        crosswalk_by_line[row["line_id"]].append(row)
    if len(memberships) != len(set(memberships)):
        fail("station-line crosswalk primary key duplicated")
    if set(crosswalk_by_line) != line_ids:
        fail("one or more canonical pilot lines have no crosswalk rows")

    lines_by_corridor = {row["pilot_corridor_id"]: row for row in rows["lines"]}
    if set(lines_by_corridor) != set(corridors):
        fail("line output does not resolve all pilot corridors")
    for corridor_id, corridor in corridors.items():
        line = lines_by_corridor[corridor_id]
        decision = segment_decisions[corridor_id]
        ordered = sorted(crosswalk_by_line[line["line_id"]], key=lambda item: item["sequence_index"])
        sequence = [row["sequence_index"] for row in ordered]
        names = [stations_by_id[row["station_id"]]["display_name_ja"] for row in ordered]
        source_order = [row["n02_station_key"] for row in ordered]
        expected_names = corridor["primary_station_order"]
        if sequence != list(range(1, len(ordered) + 1)):
            fail(f"service sequence is not contiguous: {corridor_id}")
        if names != expected_names:
            fail(f"service station order differs from the accepted rule: {corridor_id}")
        if line["resolution_status"] != "confirmed_exact_segment" or line["unresolved_station_count"] != 0:
            fail(f"service segment is not confirmed: {corridor_id}")
        if line["station_count"] != decision["station_count"] or len(ordered) != decision["station_count"]:
            fail(f"service segment count mismatch: {corridor_id}")
        if line["endpoint_start"] != decision["endpoint_start"] or line["endpoint_end"] != decision["endpoint_end"]:
            fail(f"service segment endpoint mismatch: {corridor_id}")
        if line["segment_station_order_sha256"] != sha256_json(expected_names):
            fail(f"station-order lock hash mismatch: {corridor_id}")
        if line["segment_source_keys_sha256"] != sha256_json(source_order):
            fail(f"source-key lock hash mismatch: {corridor_id}")
        recorded = manifest.get("service_segments", {}).get(corridor_id, {})
        if (
            recorded.get("station_order_sha256") != line["segment_station_order_sha256"]
            or recorded.get("source_keys_sha256") != line["segment_source_keys_sha256"]
        ):
            fail(f"manifest service lock mismatch: {corridor_id}")

    if counts.get("locked_service_segments") != 8:
        fail("manifest does not record eight locked service segments")

    if any(
        row["review_status"] != "confirmed"
        or row["transfer_basis"] != "official"
        or row["source_release_id"] != adjudication["adjudication_release_id"]
        for row in rows["hubs"]
    ):
        fail("hub remained unconfirmed or lacks official transfer basis")
    if len(hub_ids) != acceptance.get("expected_confirmed_hubs"):
        fail("confirmed hub count differs from accepted adjudication")
    links_by_hub: dict[str, set[str]] = defaultdict(set)
    for row in rows["hub_station_group_links"]:
        if row["hub_id"] not in hub_ids or row["station_group_id"] not in group_ids:
            fail("hub link foreign key unresolved")
        if row["is_manual"] != 1:
            fail("confirmed hub link lacks manual-adjudication flag")
        links_by_hub[row["hub_id"]].add(row["station_group_id"])

    group_id_by_source = {row["n02_station_group_key"]: row["station_group_id"] for row in rows["station_groups"]}
    hub_aliases = {
        row["source_key"]: row["entity_id"]
        for row in rows["entity_alias"]
        if row["entity_type"] == "hub" and row["source_namespace"] == "PHASE1_G2_ADJUDICATION"
    }
    reviews_by_source = {row["source_key"]: row for row in rows["identity_review_queue"]}
    for decision in decisions:
        source_key = decision["source_key"]
        review = reviews_by_source.get(source_key)
        if review is None or review["status"] != "resolved" or review["resolved_at"] != adjudication["adjudicated_at"]:
            fail(f"manual review is not resolved: {source_key}")
        evidence = json.loads(review["evidence_json"])
        if evidence.get("adjudication", {}).get("decision") != decision["decision"]:
            fail(f"review evidence does not preserve decision: {source_key}")
        expected_groups = {group_id_by_source[key] for key in decision["station_group_keys"]}
        target_key = decision.get("target_hub_key")
        if decision["decision"] == "confirm_hub":
            hub_id = hub_aliases.get(target_key)
            if hub_id is None or links_by_hub[hub_id] != expected_groups:
                fail(f"confirmed hub links differ from adjudication: {source_key}")
        elif decision["decision"] == "resolve_duplicate":
            if hub_aliases.get(target_key) is None:
                fail(f"duplicate resolution target is missing: {source_key}")
        elif any(expected_groups <= linked_groups for linked_groups in links_by_hub.values()):
            fail(f"rejected hub groups were nevertheless merged: {source_key}")

    allowed_issues = {"no_match", "ambiguous_match", "collision", "split_candidate", "merge_candidate"}
    if any(row["issue_type"] not in allowed_issues for row in rows["identity_review_queue"]):
        fail("identity review history contains an unknown issue type")
    if any(row["status"] != "resolved" for row in rows["identity_review_queue"]):
        fail("G2 PASS must preserve only resolved review-history rows")
    if counts.get("open_reviews") != acceptance.get("expected_remaining_open_reviews"):
        fail("manifest open-review count differs from accepted adjudication")

    n02_artifacts = [a for a in lock.get("artifacts", []) if a.get("artifact_id") == "n02-25-gml"]
    if len(n02_artifacts) != 1 or n02_artifacts[0].get("source_release_id") != "N02-25":
        fail("G1 source lock has no N02-25 artifact")
    if sha256(N02_ARCHIVE) != n02_artifacts[0].get("sha256"):
        fail("N02 archive does not match G1 source lock")

    print(
        "PASS Phase 1 G2 identity adjudication: "
        f"{len(rows['stations'])} stations, {len(rows['station_line_crosswalk'])} crosswalk rows, "
        f"{len(rows['hubs'])} confirmed hubs, 8 locked segments, 0 open reviews"
    )


if __name__ == "__main__":
    main()
