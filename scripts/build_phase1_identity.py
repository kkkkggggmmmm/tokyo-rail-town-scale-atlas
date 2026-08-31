#!/usr/bin/env python3
"""Build the adjudicated Phase 1 G2 identity layer from the locked N02 archive.

The script deliberately does not promote N02 codes to canonical IDs.  A small
persisted registry mints opaque IDs once; source keys remain in entity_alias and
the crosswalk. Service-corridor rules are explicit in
``data/reference/PHASE1_IDENTITY_RULES.yml``; manual hub and exact-segment
decisions live in ``data/reference/PHASE1_G2_ADJUDICATIONS.yml``. Missing or
ambiguous names still become review-queue records instead of silent merges.
"""

from __future__ import annotations

import hashlib
import json
import math
import uuid
import zipfile
from collections import defaultdict
from datetime import date
from itertools import combinations
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import yaml


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/raw/phase1/archives/N02-25_GML.zip"
RULES_PATH = ROOT / "data/reference/PHASE1_IDENTITY_RULES.yml"
ADJUDICATION_PATH = ROOT / "data/reference/PHASE1_G2_ADJUDICATIONS.yml"
REGISTRY_PATH = ROOT / "data/reference/PHASE1_IDENTITY_REGISTRY.yml"
DERIVED = ROOT / "data/derived"
QA = ROOT / "data/qa"
MANIFEST_PATH = ROOT / "data/manifests/identity.phase1.yml"
REPORT_PATH = ROOT / "docs/PHASE1_G2_IDENTITY_REPORT.md"
SOURCE_RELEASE_ID = "N02-25"
SOURCE_NAMESPACE = "N02_2025"
FIXED_DATE = "2026-08-31"
RUN_ID = "run_phase1_g2_adjudicated_20260831"
IDENTITY_CREATED_AT = "2026-08-30"
SOURCE_VALID_FROM = date(2025, 12, 31)
ADJUDICATION_VALID_FROM = date(2026, 8, 31)


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def station_centroid(coordinates: list[Any]) -> tuple[float, float]:
    points: list[tuple[float, float]] = []
    for point in coordinates:
        if isinstance(point, list) and len(point) >= 2 and isinstance(point[0], (int, float)):
            points.append((float(point[0]), float(point[1])))
    if not points:
        raise ValueError("station geometry has no coordinate pair")
    return (sum(x for x, _ in points) / len(points), sum(y for _, y in points) / len(points))


def approx_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    mean_lat = math.radians((a[1] + b[1]) / 2.0)
    dx = (a[0] - b[0]) * 111.32 * math.cos(mean_lat)
    dy = (a[1] - b[1]) * 111.32
    return math.hypot(dx, dy)


def load_registry() -> dict[str, Any]:
    if REGISTRY_PATH.exists():
        data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8")) or {}
    else:
        data = {}
    data.setdefault("registry_version", "0.1.0")
    data.setdefault("project_id", "tokyo-rail-town-scale-atlas")
    data.setdefault("source_release_id", SOURCE_RELEASE_ID)
    data.setdefault("minted_at", FIXED_DATE)
    data.setdefault("maps", {})
    for kind in ("line", "station", "station_group", "hub", "alias", "review"):
        data["maps"].setdefault(kind, {})
    return data


def opaque_id(registry: dict[str, Any], kind: str, key: str) -> str:
    prefixes = {
        "line": "lin",
        "station": "sta",
        "station_group": "stg",
        "hub": "hub",
        "alias": "als",
        "review": "idr",
    }
    mapping = registry["maps"][kind]
    if key not in mapping:
        mapping[key] = f"{prefixes[kind]}_{uuid.uuid4().hex}"
    return mapping[key]


def save_registry(registry: dict[str, Any]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(
        yaml.safe_dump(registry, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )


def load_n02() -> dict[str, list[dict[str, Any]]]:
    if not ARCHIVE.exists():
        raise FileNotFoundError(f"locked N02 archive missing: {ARCHIVE}")
    with zipfile.ZipFile(ARCHIVE) as archive:
        raw = archive.read("N02-25_GML/UTF-8/N02-25_Station.geojson")
    data = json.loads(raw.decode("utf-8"))
    by_source: dict[str, dict[str, Any]] = {}
    for feature_index, feature in enumerate(data.get("features", [])):
        props = feature.get("properties", {})
        operator = str(props.get("N02_004") or "").strip()
        route = str(props.get("N02_003") or "").strip()
        name = str(props.get("N02_005") or "").strip()
        station_code = str(props.get("N02_005c") or "").strip()
        group_code = str(props.get("N02_005g") or "").strip()
        if not operator or not route or not name or not station_code:
            # Preserve malformed rows in a deterministic source key so the caller
            # can surface them; no row is silently dropped from the staging parse.
            station_code = station_code or f"MISSING_{feature_index:06d}"
        source_key = f"{operator}|{route}|{station_code}"
        centroid = station_centroid(feature.get("geometry", {}).get("coordinates", []))
        existing = by_source.get(source_key)
        if existing is None:
            by_source[source_key] = {
                "source_key": source_key,
                "operator": operator,
                "route": route,
                "name": name,
                "station_code": station_code,
                "group_code": group_code,
                "centroids": [centroid],
                "feature_indexes": [feature_index],
                "name_variants": [name],
                "group_variants": [group_code],
            }
        else:
            existing["centroids"].append(centroid)
            existing["feature_indexes"].append(feature_index)
            if name not in existing["name_variants"]:
                existing["name_variants"].append(name)
            if group_code not in existing["group_variants"]:
                existing["group_variants"].append(group_code)
    records = list(by_source.values())
    for record in records:
        points = record.pop("centroids")
        record["lon"] = sum(x for x, _ in points) / len(points)
        record["lat"] = sum(y for _, y in points) / len(points)
        record["feature_count"] = len(record["feature_indexes"])
        record["centroid"] = (record["lon"], record["lat"])
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[f"{record['operator']}|{record['route']}"] .append(record)
    return grouped


def parquet_write(path: Path, rows: list[dict[str, Any]], schema: pa.Schema) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(rows, schema=schema)
    pq.write_table(table, path, compression="zstd")


def s(name: str) -> pa.Field:
    return pa.field(name, pa.string(), nullable=True)


def required_string(name: str) -> pa.Field:
    return pa.field(name, pa.string(), nullable=False)


def build() -> dict[str, Any]:
    rules = yaml.safe_load(RULES_PATH.read_text(encoding="utf-8"))
    adjudication = yaml.safe_load(ADJUDICATION_PATH.read_text(encoding="utf-8"))
    if adjudication.get("status") != "accepted" or adjudication.get("gate") != "G2":
        raise ValueError("G2 adjudication must be accepted before building confirmed artifacts")
    review_decisions = {
        row["source_key"]: row for row in adjudication.get("review_decisions", [])
    }
    segment_decisions = {
        row["corridor_id"]: row for row in adjudication.get("service_segments", [])
    }
    grouped = load_n02()
    registry = load_registry()

    corridors = rules["corridors"]
    if set(segment_decisions) != set(corridors):
        raise ValueError("G2 adjudication must lock exactly the configured pilot corridors")
    # Index records by operator/route/name and retain all source variants.
    by_name: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for route_records in grouped.values():
        for record in route_records:
            by_name[(record["operator"], record["route"], record["name"])].append(record)

    selected: dict[str, dict[str, Any]] = {}
    selected_usage: dict[str, list[dict[str, Any]]] = defaultdict(list)
    review_rows: list[dict[str, Any]] = []
    crosswalk_rows: list[dict[str, Any]] = []
    line_rows: list[dict[str, Any]] = []
    alias_rows: list[dict[str, Any]] = []
    hub_candidate_group_keys: set[str] = set()

    def add_review(
        *,
        entity_type: str,
        source_key: str,
        issue_type: str,
        candidate_ids: list[str],
        status: str,
        note: str,
        corridor_id: str | None,
        evidence: dict[str, Any],
    ) -> str:
        review_key = compact_json(
            {
                "entity_type": entity_type,
                "source_key": source_key,
                "issue_type": issue_type,
                "corridor_id": corridor_id,
            }
        )
        review_id = opaque_id(registry, "review", review_key)
        if not any(row["review_id"] == review_id for row in review_rows):
            review_rows.append(
                {
                    "review_id": review_id,
                    "entity_type": entity_type,
                    "source_release_id": SOURCE_RELEASE_ID,
                    "source_key": source_key,
                    "issue_type": issue_type,
                    "candidate_entity_ids_json": compact_json(candidate_ids),
                    "status": status,
                    "resolution_note": note,
                    "resolved_at": IDENTITY_CREATED_AT if status == "resolved" else None,
                    "pilot_corridor_id": corridor_id,
                    "evidence_json": compact_json(evidence),
                }
            )
        return review_id

    def choose_record(
        corridor_id: str,
        corridor: dict[str, Any],
        name: str,
        route: str | None,
        override: dict[str, Any] | None,
    ) -> tuple[dict[str, Any] | None, str, str | None]:
        operator = (override or {}).get("operator", corridor["operator"])
        preferred_route = route or (override or {}).get("route")
        candidates: list[dict[str, Any]] = []
        if preferred_route:
            candidates = list(by_name.get((operator, preferred_route, name), []))
        if not candidates:
            for candidate_route in corridor["source_routes"]:
                candidates.extend(by_name.get((operator, candidate_route, name), []))
        # De-duplicate the fallback union by immutable source alias.
        candidates = list({row["source_key"]: row for row in candidates}.values())
        if not candidates:
            return None, "unresolved_no_match", None
        if len(candidates) == 1:
            status = "confirmed_manual_extension" if override else "confirmed_source_route"
            return candidates[0], status, None
        group_keys = {row["group_code"] for row in candidates}
        if len(group_keys) == 1 and "" not in group_keys:
            candidates.sort(key=lambda row: row["source_key"])
            status = "confirmed_same_group_seed" if not override else "confirmed_manual_extension"
            return candidates[0], status, None
        ids = [opaque_id(registry, "station", row["source_key"]) for row in sorted(candidates, key=lambda r: r["source_key"])]
        review_id = add_review(
            entity_type="station",
            source_key=f"{corridor_id}|{name}",
            issue_type="ambiguous_match",
            candidate_ids=ids,
            status="open",
            note="複数のN02 source aliasが異なるgroup seedを持つため自動選択しない。",
            corridor_id=corridor_id,
            evidence={"operator": operator, "route": preferred_route, "candidate_source_keys": [r["source_key"] for r in candidates]},
        )
        return None, "unresolved_ambiguous", review_id

    def register_station(record: dict[str, Any], corridor_id: str, inclusion_status: str) -> str:
        key = record["source_key"]
        station_id = opaque_id(registry, "station", key)
        if key not in selected:
            selected[key] = {
                "record": record,
                "station_id": station_id,
                "inclusion_statuses": set(),
                "corridors": set(),
                "resolution_statuses": set(),
            }
        selected[key]["inclusion_statuses"].add(inclusion_status)
        selected[key]["corridors"].add(corridor_id)
        return station_id

    for corridor_id, corridor in corridors.items():
        line_id = opaque_id(registry, "line", corridor_id)
        primary_names = corridor["primary_station_order"]
        route_preference = corridor.get("route_preference", {})
        overrides = corridor.get("source_route_overrides", {})
        previous_point: tuple[float, float] | None = None
        cumulative_km = 0.0
        unresolved = 0
        emitted = 0
        for sequence_index, name in enumerate(primary_names, start=1):
            override = overrides.get(name)
            preferred_route = route_preference.get(name)
            record, resolution_status, review_id = choose_record(
                corridor_id, corridor, name, preferred_route, override
            )
            if record is None:
                unresolved += 1
                if review_id is None:
                    review_id = add_review(
                        entity_type="station",
                        source_key=f"{corridor_id}|{name}",
                        issue_type="no_match",
                        candidate_ids=[],
                        status="open",
                        note="指定されたpilot sequenceの駅名に一致するN02 source rowがない。",
                        corridor_id=corridor_id,
                        evidence={"operator": corridor["operator"], "source_routes": corridor["source_routes"]},
                    )
                continue
            station_id = register_station(record, corridor_id, "primary")
            selected[record["source_key"]]["resolution_statuses"].add(resolution_status)
            selected_usage[record["source_key"]].append(
                {
                    "corridor_id": corridor_id,
                    "line_id": line_id,
                    "sequence_index": sequence_index,
                    "resolution_status": resolution_status,
                    "review_id": review_id,
                    "inclusion_status": "primary",
                }
            )
            point = record["centroid"]
            if previous_point is not None:
                cumulative_km += approx_km(previous_point, point)
            previous_point = point
            group_key = record["group_code"] or f"missing:{record['source_key']}"
            crosswalk_rows.append(
                {
                    "station_id": station_id,
                    "station_group_id": opaque_id(registry, "station_group", group_key),
                    "hub_id": None,
                    "line_id": line_id,
                    "sequence_index": sequence_index,
                    "distance_from_origin_km": round(cumulative_km, 6),
                    "membership_valid_from": SOURCE_VALID_FROM,
                    "membership_valid_to": None,
                    "n02_source_release_id": SOURCE_RELEASE_ID,
                    "n02_station_key": record["source_key"],
                    "n02_station_group_key": record["group_code"] or None,
                    "n02_operator_key": record["operator"],
                    "n02_route_key": record["route"],
                    "identity_resolution_status": resolution_status,
                    "identity_review_id": review_id,
                    "pilot_corridor_id": corridor_id,
                    "segment_inclusion_status": "primary_confirmed",
                    "distance_method": "geodesic_centroid_chain_candidate",
                }
            )
            emitted += 1

            # A source-route override is a deliberate cross-route service extension;
            # record the resolution even when the source row itself is unambiguous.
            if override:
                add_review(
                    entity_type="station",
                    source_key=record["source_key"],
                    issue_type="merge_candidate",
                    candidate_ids=[station_id],
                    status="resolved",
                    note=override.get("reason", "pilot service endpoint extension"),
                    corridor_id=corridor_id,
                    evidence={"override": override, "n02_group_code": record["group_code"]},
                )

        # Keep slow-line context visible in station candidates, but do not put it
        # into the rapid primary crosswalk.
        for name in corridor.get("auxiliary_station_names", []):
            record, resolution_status, _ = choose_record(corridor_id, corridor, name, None, None)
            if record is not None:
                register_station(record, corridor_id, "auxiliary_context")
                selected[record["source_key"]]["resolution_statuses"].add(resolution_status)
                selected_usage[record["source_key"]].append(
                    {
                        "corridor_id": corridor_id,
                        "line_id": line_id,
                        "sequence_index": None,
                        "resolution_status": "context_only",
                        "review_id": None,
                        "inclusion_status": "auxiliary_context",
                    }
                )

        segment_decision = segment_decisions[corridor_id]
        if segment_decision.get("decision") != "confirmed_exact_segment":
            raise ValueError(f"service segment is not confirmed: {corridor_id}")
        if (
            segment_decision.get("endpoint_start") != corridor["endpoint_start"]
            or segment_decision.get("endpoint_end") != corridor["endpoint_end"]
            or int(segment_decision.get("station_count", -1)) != len(primary_names)
        ):
            raise ValueError(f"service segment lock conflicts with identity rule: {corridor_id}")
        if unresolved or emitted != len(primary_names):
            raise ValueError(f"cannot confirm an incomplete service segment: {corridor_id}")
        line_rows.append(
            {
                "line_id": line_id,
                "display_name_ja": corridor["display_name_ja"],
                "operator_id": corridor["operator"],
                "line_kind": "analysis_corridor",
                "lifecycle_status": "active",
                "pilot_corridor_id": corridor_id,
                "source_route_keys_json": compact_json(corridor["source_routes"]),
                "endpoint_start": corridor["endpoint_start"],
                "endpoint_end": corridor["endpoint_end"],
                "resolution_status": "confirmed_exact_segment",
                "inclusion_status": corridor["inclusion_status"],
                "station_count": emitted,
                "unresolved_station_count": unresolved,
                "rule_version": rules["rules_version"],
                "source_release_id": SOURCE_RELEASE_ID,
                "segment_station_order_sha256": sha256_bytes(compact_json(primary_names).encode("utf-8")),
                "segment_source_keys_sha256": "",
                "segment_lock_version": adjudication["adjudication_version"],
                "segment_evidence_json": compact_json(segment_decision.get("evidence", [])),
            }
        )

    # Keep well-known different-name transfer pairs in the review queue.  They
    # are deliberately not turned into a hub row until external transfer
    # evidence is adjudicated.  Their source station aliases are retained as
    # context candidates so the eventual decision can be made without a new
    # opaque-ID mint.
    for candidate in rules.get("manual_hub_candidates", []):
        candidate_station_ids: list[str] = []
        missing_refs: list[dict[str, Any]] = []
        for ref in candidate.get("station_refs", []):
            ref_rows = by_name.get((ref["operator"], ref["route"], ref["name"]), [])
            if len(ref_rows) == 1:
                candidate_station_ids.append(register_station(ref_rows[0], f"hub_context:{candidate['hub_key']}", "hub_context"))
            elif not ref_rows:
                missing_refs.append(ref)
            else:
                candidate_station_ids.extend(opaque_id(registry, "station", row["source_key"]) for row in ref_rows)
                missing_refs.append(ref)
        issue_type = "no_match" if missing_refs else "merge_candidate"
        status = "open"
        note = (
            "異名駅のhub候補。公式transfer evidenceまたは案内徒歩経路を確認するまで自動統合しない。"
            if not missing_refs
            else "hub候補の参照駅にN02 source rowがない、または複数候補があるため自動統合しない。"
        )
        add_review(
            entity_type="hub",
            source_key=f"manual:{candidate['hub_key']}",
            issue_type=issue_type,
            candidate_ids=sorted(set(candidate_station_ids)),
            status=status,
            note=note,
            corridor_id=None,
            evidence={"display_name_ja": candidate["display_name_ja"], "station_refs": candidate.get("station_refs", []), "evidence_required": candidate.get("evidence_required")},
        )

    # Group candidates and detect source-seed collisions/nearby same-name cases.
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in selected.values():
        record = item["record"]
        group_key = record["group_code"] or f"missing:{record['source_key']}"
        groups[group_key].append(item)

    for group_key, members in sorted(groups.items()):
        group_id = opaque_id(registry, "station_group", group_key)
        names = sorted({item["record"]["name"] for item in members})
        operators = sorted({item["record"]["operator"] for item in members})
        routes = sorted({item["record"]["route"] for item in members})
        station_ids = sorted(item["station_id"] for item in members)
        if len(names) > 1:
            add_review(
                entity_type="station_group",
                source_key=group_key,
                issue_type="merge_candidate",
                candidate_ids=station_ids,
                status="open",
                note="同一N02 group seedに複数名称があるため、公開駅群への確定前に監査する。",
                corridor_id=None,
                evidence={"names": names, "operators": operators, "routes": routes},
            )
        if len(operators) > 1 or len(routes) > 1:
            hub_candidate_group_keys.add(group_key)
        for item in members:
            for usage in selected_usage[item["record"]["source_key"]]:
                for row in crosswalk_rows:
                    if row["station_id"] == item["station_id"] and row["line_id"] == usage["line_id"]:
                        row["station_group_id"] = group_id
        # Alias for the N02 group seed is retained separately from the station alias.
        alias_key = f"station_group|{group_key}"
        alias_rows.append(
            {
                "entity_alias_id": opaque_id(registry, "alias", alias_key),
                "entity_type": "station_group",
                "entity_id": group_id,
                "source_release_id": SOURCE_RELEASE_ID,
                "source_namespace": SOURCE_NAMESPACE,
                "source_key": group_key,
                "source_name": names[0] if names else None,
                "valid_from": SOURCE_VALID_FROM,
                "valid_to": None,
                "match_method": "exact_source_seed",
                "match_confidence": 0.8,
                "review_status": "confirmed",
            }
        )

    # Same-name, distinct-group near collisions are never auto-merged.
    station_items = list(selected.values())
    for left, right in combinations(station_items, 2):
        a, b = left["record"], right["record"]
        if a["name"] != b["name"] or a["group_code"] == b["group_code"]:
            continue
        if approx_km(a["centroid"], b["centroid"]) <= 0.3:
            add_review(
                entity_type="station_group",
                source_key=f"{a['name']}|{a['source_key']}|{b['source_key']}",
                issue_type="ambiguous_match",
                candidate_ids=[left["station_id"], right["station_id"]],
                status="open",
                note="同名だがN02 group seedが異なる近接station node。自動統合しない。",
                corridor_id=None,
                evidence={"distance_m": round(approx_km(a["centroid"], b["centroid"]) * 1000, 1)},
            )

    hub_rows: list[dict[str, Any]] = []
    hub_link_rows: list[dict[str, Any]] = []
    for group_key in sorted(hub_candidate_group_keys):
        members = groups[group_key]
        group_id = opaque_id(registry, "station_group", group_key)
        hub_id = opaque_id(registry, "hub", f"group:{group_key}")
        names = sorted({item["record"]["name"] for item in members})
        operators = sorted({item["record"]["operator"] for item in members})
        routes = sorted({item["record"]["route"] for item in members})
        evidence = {
            "basis": "N02 same-name group seed plus multiple operator/route aliases",
            "source_group_key": group_key,
            "operators": operators,
            "routes": routes,
            "confirmation_required": "manual_transfer_evidence",
        }
        hub_rows.append(
            {
                "hub_id": hub_id,
                "display_name_ja": names[0] if names else group_key,
                "transfer_basis": "manual",
                "review_status": "candidate",
                "source_release_id": SOURCE_RELEASE_ID,
                "station_group_id": group_id,
                "n02_station_group_key": group_key,
                "operator_keys_json": compact_json(operators),
                "route_keys_json": compact_json(routes),
                "evidence_json": compact_json(evidence),
            }
        )
        hub_link_rows.append(
            {
                "hub_id": hub_id,
                "station_group_id": group_id,
                "walking_distance_m": None,
                "evidence_json": compact_json(evidence),
                "is_manual": 0,
            }
        )
        add_review(
            entity_type="hub",
            source_key=group_key,
            issue_type="merge_candidate",
            candidate_ids=[hub_id],
            status="open",
            note="N02 group seedはhubの候補であり、異名乗換を含む確定根拠ではない。手動のtransfer evidenceが必要。",
            corridor_id=None,
            evidence=evidence,
        )

    # Apply the accepted, source-cited hub decisions. The decision file, rather
    # than proximity or N02 grouping alone, is the authority for confirmation.
    open_source_keys = {row["source_key"] for row in review_rows if row["status"] == "open"}
    if open_source_keys != set(review_decisions):
        missing = sorted(open_source_keys - set(review_decisions))
        extra = sorted(set(review_decisions) - open_source_keys)
        raise ValueError(f"G2 review decision coverage mismatch; missing={missing}, extra={extra}")

    hubs_by_key = {f"group:{row['n02_station_group_key']}": row for row in hub_rows}
    links_by_hub = defaultdict(list)
    for link in hub_link_rows:
        links_by_hub[link["hub_id"]].append(link)

    for decision in review_decisions.values():
        action = decision["decision"]
        target_key = decision.get("target_hub_key")
        if action in {"confirm_hub", "resolve_duplicate"} and not target_key:
            raise ValueError(f"hub decision has no target: {decision['source_key']}")

        if action == "confirm_hub" and target_key not in hubs_by_key:
            group_keys = decision.get("station_group_keys", [])
            if len(group_keys) < 2:
                raise ValueError(f"new manual hub must link at least two groups: {target_key}")
            unknown_groups = sorted(set(group_keys) - set(groups))
            if unknown_groups:
                raise ValueError(f"manual hub refers to unknown groups: {unknown_groups}")
            members = [item for group_key in group_keys for item in groups[group_key]]
            hub_id = opaque_id(registry, "hub", target_key)
            evidence = {
                "basis": "accepted G2 manual adjudication",
                "adjudication_version": adjudication["adjudication_version"],
                "decision": decision,
            }
            hub_row = {
                "hub_id": hub_id,
                "display_name_ja": decision["display_name_ja"],
                "transfer_basis": decision["transfer_basis"],
                "review_status": "confirmed",
                "source_release_id": adjudication["adjudication_release_id"],
                "station_group_id": None,
                "n02_station_group_key": None,
                "operator_keys_json": compact_json(sorted({item["record"]["operator"] for item in members})),
                "route_keys_json": compact_json(sorted({item["record"]["route"] for item in members})),
                "evidence_json": compact_json(evidence),
            }
            hub_rows.append(hub_row)
            hubs_by_key[target_key] = hub_row
            for group_key in group_keys:
                link = {
                    "hub_id": hub_id,
                    "station_group_id": opaque_id(registry, "station_group", group_key),
                    "walking_distance_m": None,
                    "evidence_json": compact_json(evidence),
                    "is_manual": 1,
                }
                hub_link_rows.append(link)
                links_by_hub[hub_id].append(link)

        if action == "confirm_hub":
            hub_row = hubs_by_key[target_key]
            evidence = {
                "basis": "accepted G2 manual adjudication",
                "adjudication_version": adjudication["adjudication_version"],
                "decision": decision,
            }
            hub_row["transfer_basis"] = decision["transfer_basis"]
            hub_row["review_status"] = "confirmed"
            hub_row["source_release_id"] = adjudication["adjudication_release_id"]
            hub_row["evidence_json"] = compact_json(evidence)
            for link in links_by_hub[hub_row["hub_id"]]:
                link["evidence_json"] = compact_json(evidence)
                link["is_manual"] = 1
        elif action == "resolve_duplicate":
            if target_key not in hubs_by_key:
                raise ValueError(f"duplicate decision target is unknown: {target_key}")
        elif action != "reject_hub":
            raise ValueError(f"unknown hub decision: {action}")

    for row in review_rows:
        if row["status"] != "open":
            continue
        decision = review_decisions[row["source_key"]]
        row["status"] = "resolved"
        row["resolved_at"] = adjudication["adjudicated_at"]
        row["resolution_note"] = decision["resolution_note"]
        original_evidence = json.loads(row["evidence_json"])
        original_evidence["adjudication"] = decision
        target_key = decision.get("target_hub_key")
        if target_key:
            original_evidence["resolved_hub_id"] = hubs_by_key[target_key]["hub_id"]
        row["evidence_json"] = compact_json(original_evidence)

    if any(row["status"] == "open" for row in review_rows):
        raise ValueError("G2 cannot pass with an open identity review")

    for target_key, hub_row in sorted(hubs_by_key.items()):
        alias_key = f"hub|{target_key}"
        alias_rows.append(
            {
                "entity_alias_id": opaque_id(registry, "alias", alias_key),
                "entity_type": "hub",
                "entity_id": hub_row["hub_id"],
                "source_release_id": adjudication["adjudication_release_id"],
                "source_namespace": "PHASE1_G2_ADJUDICATION",
                "source_key": target_key,
                "source_name": hub_row["display_name_ja"],
                "valid_from": ADJUDICATION_VALID_FROM,
                "valid_to": None,
                "match_method": "manual_adjudication",
                "match_confidence": 1.0,
                "review_status": "confirmed",
            }
        )

    # Patch crosswalk hub references only after all confirmed links are known.
    group_to_hub: dict[str, str] = {}
    for link in hub_link_rows:
        if link["station_group_id"] in group_to_hub:
            raise ValueError(f"station group linked to multiple G2 hubs: {link['station_group_id']}")
        group_to_hub[link["station_group_id"]] = link["hub_id"]
    for row in crosswalk_rows:
        row["hub_id"] = group_to_hub.get(row["station_group_id"])

    station_rows: list[dict[str, Any]] = []
    member_rows: list[dict[str, Any]] = []
    for key, item in sorted(selected.items()):
        record = item["record"]
        station_id = item["station_id"]
        group_key = record["group_code"] or f"missing:{key}"
        station_rows.append(
            {
                "station_id": station_id,
                "display_name_ja": record["name"],
                "operator_id": record["operator"],
                "station_kind": "unknown",
                "lifecycle_status": "active",
                "valid_from": SOURCE_VALID_FROM,
                "valid_to": None,
                "centroid_lon": record["lon"],
                "centroid_lat": record["lat"],
                "geometry_crs": "EPSG:6668",
                "created_at": IDENTITY_CREATED_AT,
                "n02_source_release_id": SOURCE_RELEASE_ID,
                "n02_station_key": key,
                "n02_station_group_key": record["group_code"] or None,
                "n02_operator_key": record["operator"],
                "n02_route_key": record["route"],
                "source_feature_count": record["feature_count"],
                "pilot_corridor_ids_json": compact_json(sorted(item["corridors"])),
                "inclusion_status": "+".join(sorted(item["inclusion_statuses"])),
                "identity_resolution_status": "+".join(sorted(item["resolution_statuses"])) or "confirmed_source_identity",
            }
        )
        group_id = opaque_id(registry, "station_group", group_key)
        member_rows.append(
            {
                "station_group_id": group_id,
                "station_id": station_id,
                "membership_basis": "n02_same_name_300m_source_seed",
                "confidence": 0.8,
                "review_status": "confirmed",
                "source_release_id": SOURCE_RELEASE_ID,
                "n02_station_group_key": record["group_code"] or None,
            }
        )
        alias_key = f"station|{key}"
        alias_rows.append(
            {
                "entity_alias_id": opaque_id(registry, "alias", alias_key),
                "entity_type": "station",
                "entity_id": station_id,
                "source_release_id": SOURCE_RELEASE_ID,
                "source_namespace": SOURCE_NAMESPACE,
                "source_key": key,
                "source_name": record["name"],
                "valid_from": SOURCE_VALID_FROM,
                "valid_to": None,
                "match_method": "exact_source_seed",
                "match_confidence": 0.95,
                "review_status": "confirmed",
            }
        )

    for corridor_id, corridor in corridors.items():
        line_id = opaque_id(registry, "line", corridor_id)
        alias_key = f"line|{corridor['operator']}|{corridor_id}"
        alias_rows.append(
            {
                "entity_alias_id": opaque_id(registry, "alias", alias_key),
                "entity_type": "line",
                "entity_id": line_id,
                "source_release_id": SOURCE_RELEASE_ID,
                "source_namespace": SOURCE_NAMESPACE,
                "source_key": f"{corridor['operator']}|{','.join(corridor['source_routes'])}",
                "source_name": corridor["display_name_ja"],
                "valid_from": SOURCE_VALID_FROM,
                "valid_to": None,
                "match_method": "crosswalk",
                "match_confidence": 0.85 if len(corridor["source_routes"]) > 1 else 0.95,
                "review_status": "confirmed",
            }
        )

    # Patch line and group aliases are sorted/deduplicated before writing.
    def unique_rows(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
        by_key: dict[Any, dict[str, Any]] = {}
        for row in rows:
            by_key[row[key]] = row
        return [by_key[k] for k in sorted(by_key)]

    crosswalk_by_line: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in crosswalk_rows:
        crosswalk_by_line[row["line_id"]].append(row)
    for row in line_rows:
        ordered = sorted(crosswalk_by_line[row["line_id"]], key=lambda item: item["sequence_index"])
        source_keys = [item["n02_station_key"] for item in ordered]
        if len(source_keys) != row["station_count"]:
            raise ValueError(f"line/crosswalk count mismatch: {row['pilot_corridor_id']}")
        row["segment_source_keys_sha256"] = sha256_bytes(compact_json(source_keys).encode("utf-8"))

    station_schema = pa.schema(
        [
            required_string("station_id"), required_string("display_name_ja"), required_string("operator_id"),
            required_string("station_kind"), required_string("lifecycle_status"), pa.field("valid_from", pa.date32(), nullable=True), pa.field("valid_to", pa.date32(), nullable=True),
            pa.field("centroid_lon", pa.float64(), nullable=False), pa.field("centroid_lat", pa.float64(), nullable=False),
            required_string("geometry_crs"), required_string("created_at"), required_string("n02_source_release_id"),
            required_string("n02_station_key"), s("n02_station_group_key"), required_string("n02_operator_key"),
            required_string("n02_route_key"), pa.field("source_feature_count", pa.int32(), nullable=False),
            required_string("pilot_corridor_ids_json"), required_string("inclusion_status"), required_string("identity_resolution_status"),
        ]
    )
    group_schema = pa.schema(
        [required_string("station_group_id"), required_string("display_name_ja"), required_string("group_rule"),
         required_string("review_status"), required_string("n02_station_group_key"), pa.field("member_count", pa.int32(), nullable=False),
         required_string("source_release_id"), required_string("source_name_variants_json"), required_string("operator_keys_json"),
         required_string("route_keys_json"), required_string("station_ids_json")]
    )
    group_rows = []
    for group_key, members in sorted(groups.items()):
        names = sorted({item["record"]["name"] for item in members})
        group_rows.append(
            {
                "station_group_id": opaque_id(registry, "station_group", group_key),
                "display_name_ja": names[0] if names else group_key,
                "group_rule": "source_seed",
                "review_status": "confirmed",
                "n02_station_group_key": group_key,
                "member_count": len(members),
                "source_release_id": SOURCE_RELEASE_ID,
                "source_name_variants_json": compact_json(names),
                "operator_keys_json": compact_json(sorted({item["record"]["operator"] for item in members})),
                "route_keys_json": compact_json(sorted({item["record"]["route"] for item in members})),
                "station_ids_json": compact_json(sorted(item["station_id"] for item in members)),
            }
        )
    line_schema = pa.schema(
        [required_string("line_id"), required_string("display_name_ja"), required_string("operator_id"), required_string("line_kind"),
         required_string("lifecycle_status"), required_string("pilot_corridor_id"), required_string("source_route_keys_json"),
         required_string("endpoint_start"), required_string("endpoint_end"), required_string("resolution_status"),
         required_string("inclusion_status"), pa.field("station_count", pa.int32(), nullable=False),
         pa.field("unresolved_station_count", pa.int32(), nullable=False), required_string("rule_version"), required_string("source_release_id"),
         required_string("segment_station_order_sha256"), required_string("segment_source_keys_sha256"),
         required_string("segment_lock_version"), required_string("segment_evidence_json")]
    )
    member_schema = pa.schema(
        [required_string("station_group_id"), required_string("station_id"), required_string("membership_basis"),
         pa.field("confidence", pa.float64(), nullable=True), required_string("review_status"), required_string("source_release_id"), s("n02_station_group_key")]
    )
    crosswalk_schema = pa.schema(
        [required_string("station_id"), required_string("station_group_id"), s("hub_id"), required_string("line_id"),
         pa.field("sequence_index", pa.int32(), nullable=True), pa.field("distance_from_origin_km", pa.float64(), nullable=True),
         pa.field("membership_valid_from", pa.date32(), nullable=True), pa.field("membership_valid_to", pa.date32(), nullable=True), required_string("n02_source_release_id"), required_string("n02_station_key"),
         s("n02_station_group_key"), required_string("n02_operator_key"), required_string("n02_route_key"), required_string("identity_resolution_status"),
         s("identity_review_id"), required_string("pilot_corridor_id"), required_string("segment_inclusion_status"), required_string("distance_method")]
    )
    alias_schema = pa.schema(
        [required_string("entity_alias_id"), required_string("entity_type"), required_string("entity_id"), required_string("source_release_id"),
         required_string("source_namespace"), required_string("source_key"), s("source_name"), pa.field("valid_from", pa.date32(), nullable=True), pa.field("valid_to", pa.date32(), nullable=True),
         required_string("match_method"), pa.field("match_confidence", pa.float64(), nullable=True), required_string("review_status")]
    )
    review_schema = pa.schema(
        [required_string("review_id"), required_string("entity_type"), required_string("source_release_id"), required_string("source_key"),
         required_string("issue_type"), required_string("candidate_entity_ids_json"), required_string("status"), s("resolution_note"),
         s("resolved_at"), s("pilot_corridor_id"), required_string("evidence_json")]
    )
    hub_schema = pa.schema(
        [required_string("hub_id"), required_string("display_name_ja"), required_string("transfer_basis"), required_string("review_status"),
         required_string("source_release_id"), s("station_group_id"), s("n02_station_group_key"),
         required_string("operator_keys_json"), required_string("route_keys_json"), required_string("evidence_json")]
    )
    hub_link_schema = pa.schema(
        [required_string("hub_id"), required_string("station_group_id"), pa.field("walking_distance_m", pa.float64(), nullable=True),
         required_string("evidence_json"), pa.field("is_manual", pa.int8(), nullable=False)]
    )

    DERIVED.mkdir(parents=True, exist_ok=True)
    QA.mkdir(parents=True, exist_ok=True)
    outputs = {
        "stations": DERIVED / "stations.parquet",
        "station_groups": DERIVED / "station_groups.parquet",
        "hubs": DERIVED / "hubs.parquet",
        "hub_station_group_links": DERIVED / "hub_station_group_links.parquet",
        "lines": DERIVED / "lines.parquet",
        "station_line_crosswalk": DERIVED / "station_line_crosswalk.parquet",
        "station_group_members": DERIVED / "station_group_members.parquet",
        "entity_alias": DERIVED / "entity_alias.parquet",
        "identity_review_queue": QA / "identity_review_queue.parquet",
    }
    parquet_write(outputs["stations"], station_rows, station_schema)
    parquet_write(outputs["station_groups"], group_rows, group_schema)
    parquet_write(outputs["hubs"], hub_rows, hub_schema)
    parquet_write(outputs["hub_station_group_links"], hub_link_rows, hub_link_schema)
    parquet_write(outputs["lines"], sorted(line_rows, key=lambda r: r["pilot_corridor_id"]), line_schema)
    parquet_write(outputs["station_line_crosswalk"], sorted(crosswalk_rows, key=lambda r: (r["line_id"], r["sequence_index"])), crosswalk_schema)
    parquet_write(outputs["station_group_members"], sorted(member_rows, key=lambda r: (r["station_group_id"], r["station_id"])), member_schema)
    parquet_write(outputs["entity_alias"], unique_rows(alias_rows, "entity_alias_id"), alias_schema)
    parquet_write(outputs["identity_review_queue"], sorted(review_rows, key=lambda r: r["review_id"]), review_schema)

    save_registry(registry)
    file_hashes = {name: sha256_bytes(path.read_bytes()) for name, path in outputs.items()}
    segment_manifest = {}
    for row in sorted(line_rows, key=lambda item: item["pilot_corridor_id"]):
        segment_manifest[row["pilot_corridor_id"]] = {
            "status": row["resolution_status"],
            "endpoint_start": row["endpoint_start"],
            "endpoint_end": row["endpoint_end"],
            "station_count": row["station_count"],
            "station_order_sha256": row["segment_station_order_sha256"],
            "source_keys_sha256": row["segment_source_keys_sha256"],
        }
    manifest = {
        "manifest_version": "0.2.0",
        "project_id": "tokyo-rail-town-scale-atlas",
        "phase": 1,
        "gate": "G2",
        "status": "PASS",
        "generated_at": FIXED_DATE,
        "run_id": RUN_ID,
        "source_release_id": SOURCE_RELEASE_ID,
        "source_archive": "data/raw/phase1/archives/N02-25_GML.zip",
        "rules": str(RULES_PATH.relative_to(ROOT)),
        "rules_sha256": sha256_bytes(RULES_PATH.read_bytes()),
        "adjudication": str(ADJUDICATION_PATH.relative_to(ROOT)),
        "adjudication_sha256": sha256_bytes(ADJUDICATION_PATH.read_bytes()),
        "identity_registry": str(REGISTRY_PATH.relative_to(ROOT)),
        "counts": {
            "pilot_corridors": len(corridors),
            "stations": len(station_rows),
            "station_groups": len(group_rows),
            "hubs": len(hub_rows),
            "lines": len(line_rows),
            "crosswalk_rows": len(crosswalk_rows),
            "review_queue": len(review_rows),
            "open_reviews": sum(row["status"] == "open" for row in review_rows),
            "resolved_reviews": sum(row["status"] == "resolved" for row in review_rows),
            "confirmed_hubs": sum(row["review_status"] == "confirmed" for row in hub_rows),
            "locked_service_segments": sum(row["resolution_status"] == "confirmed_exact_segment" for row in line_rows),
        },
        "service_segments": segment_manifest,
        "outputs": {
            name: {"path": str(path.relative_to(ROOT)), "sha256": file_hashes[name]}
            for name, path in outputs.items()
        },
        "guardrails": {
            "source_codes_as_canonical_ids": False,
            "automatic_hub_confirmation": False,
            "manual_decisions_have_cited_evidence": True,
            "ambiguous_rows_forced": False,
            "distance_method_is_sales_km": False,
            "publication_unblocked": False,
        },
    }
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False), encoding="utf-8")

    decision_labels = {
        "confirm_hub": "hub確定",
        "reject_hub": "hub不成立（分離維持）",
        "resolve_duplicate": "既存hubへ重複統合",
    }
    report_lines = [
        "# Phase 1 G2 identity report — 2026-08-31",
        "",
        "## 判定",
        "",
        "**PASS — G2を閉じ、G3へ進める。** 2026-08-30のcanonical `main`（`0607003`）に残っていた12件を、現行の事業者公式情報とロック済みN02-25により全件判定した。8回廊のexact service segmentも駅順とsource-key列のSHA-256付きで固定した。",
        "",
        "N02の同名300m group seedや近接だけではhubを確定していない。各confirm/rejectは `data/reference/PHASE1_G2_ADJUDICATIONS.yml` の公式根拠に従い、履歴行は削除せずreview queueで `resolved` とした。",
        "",
        "## 件数",
        "",
        f"- pilot回廊: {len(corridors)}",
        f"- confirmed station node: {len(station_rows)}",
        f"- confirmed station_group: {len(group_rows)}",
        f"- confirmed hub: {len(hub_rows)}",
        f"- confirmed station-line crosswalk: {len(crosswalk_rows)}",
        f"- identity review queue: {len(review_rows)}（open 0 / resolved {sum(row['status'] == 'resolved' for row in review_rows)}）",
        "",
        "## 12件の判定",
        "",
        "| source key | 表示 | 判定 |",
        "|---|---|---|",
    ]
    for decision in adjudication["review_decisions"]:
        report_lines.append(
            f"| `{decision['source_key']}` | {decision['display_name_ja']} | {decision_labels[decision['decision']]} |"
        )
    report_lines.extend(
        [
        "",
        "結果は既存9 hubを確定、朝霞台—北朝霞を2 station_groupからなるhubとして追加、浅草（銀座線—TX）は公式乗換の相互記載がないため分離維持、町田の手動候補は既存 `004387` hubへの重複として解消した。",
        "",
        "## Exact service segments",
        "",
        "| corridor | endpoints | stations | status |",
        "|---|---|---:|---|",
        ]
    )
    for segment in adjudication["service_segments"]:
        report_lines.append(
            f"| `{segment['corridor_id']}` | {segment['endpoint_start']}—{segment['endpoint_end']} | {segment['station_count']} | `confirmed_exact_segment` |"
        )
    report_lines.extend(
        [
        "",
        "中央快速線は候補20駅をそのまま承認せず、公式の東京—高尾24駅へ修正した。高円寺・阿佐ヶ谷・荻窪・西荻窪をprimaryへ移し、中央・総武緩行だけの8駅は `auxiliary_context` に残した。京浜東北・根岸線は3つのN02 physical route aliasを跨ぐ大宮—大船42駅のservice corridorとして固定した。",
        "",
        "東武東上線は現行の公式路線別ページが駅名付きで列挙する39駅を採用した。同社会社概要の集計値40との定義差はadjudicationに残し、駅ノード選択には直接列挙を優先した。",
        "",
        "## 成果物",
        "",
        "- `data/reference/PHASE1_G2_ADJUDICATIONS.yml`",
        "- `data/derived/stations.parquet`",
        "- `data/derived/station_groups.parquet`",
        "- `data/derived/hubs.parquet`",
        "- `data/derived/hub_station_group_links.parquet`",
        "- `data/derived/lines.parquet`",
        "- `data/derived/station_line_crosswalk.parquet`",
        "- `data/derived/entity_alias.parquet`",
        "- `data/qa/identity_review_queue.parquet`",
        "- `data/manifests/identity.phase1.yml`",
        "",
        "## G3 handoff",
        "",
        "G3はこのconfirmed crosswalkを入力としてmesh table・公式mesh geometry・S12 code・L01 pointを正規化できる。中心地、スコア、ランキング、公開UIは引き続き生成しておらず、publication gateは閉じたまま。",
        "",
        "参照: `data/reference/PHASE1_G2_ADJUDICATIONS.yml`, `data/reference/PHASE1_IDENTITY_RULES.yml`, `data/reference/PHASE1_IDENTITY_REGISTRY.yml`, `data/manifests/source_lock.phase1.yml`",
        ]
    )
    REPORT_PATH.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    result = build()
    print(
        "PASS Phase 1 G2 identity adjudication: "
        f"{result['counts']['stations']} stations, {result['counts']['crosswalk_rows']} crosswalk rows, "
        f"{result['counts']['open_reviews']} open reviews"
    )
