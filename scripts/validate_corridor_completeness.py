#!/usr/bin/env python3
"""Screen the frozen pilot segments for missing N02 route stations.

The G2 identity validator compares each segment with the same hand-written station
list that produced it, so it cannot notice an omitted station. This clone-safe screen
compares each segment with the N02-25 station records of the DEC-0018 metro browse
scope (`dist/network.json`), which were selected by a coordinate polygon rather than
by the hand-written lists. `data/derived/stations.parquet` is the G2 output under test;
it only supplies segment and auxiliary rows, so it adds no independent evidence.

A record on a corridor's operator and source route that lies between two consecutive
segment stations (detour ratio at most `detour_ratio_max`) must be a segment station,
an auxiliary context station, a proposed exclusion, or a recorded pending insertion.

Limits, reported rather than hidden:
- Segment edges with an endpoint outside the browse polygon have no independent
  records, so they are not screened. They must match `detection.unscreened_sections`.
- Several adjacent omissions can raise the chord ratio above the threshold, so a
  multi-station omission may be reported only partly. A walk along N02 route order
  with the raw bundle mounted is the complete check.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_public_network import inside  # noqa: E402  (the DEC-0018 scope rule)

RULES = ROOT / "data/reference/PHASE1_IDENTITY_RULES.yml"
STATIONS = ROOT / "data/derived/stations.parquet"
CROSSWALK = ROOT / "data/derived/station_line_crosswalk.parquet"
NETWORK = ROOT / "dist/network.json"
NETWORK_REGISTRY = ROOT / "data/reference/NETWORK_IDENTITY_REGISTRY.json"
CORRECTION = ROOT / "data/reference/G2_CORRIDOR_CORRECTION_2026-09-28.yml"
REGISTER = ROOT / "decisions/DECISION_REGISTER.md"
PENDING_STATUSES = {"PENDING_OWNER_DECISION", "PENDING_REGENERATION"}
STATUSES = PENDING_STATUSES | {"APPLIED"}
DECISION_ID = re.compile(r"^(DEC-\d{4}|OWNER-\d{4}-\d{2}-\d{2}-[A-Z0-9-]+)$")
RATIO_RANGE = (1.25, 1.35)
SAME_STATION_KM = 0.5
SPEC_KEYS = ["locked_count_before", "corrected_count", "insertions", "source_keys", "reuse_ids"]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    require(isinstance(value, dict), f"Expected YAML mapping: {path}")
    return value


def approx_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    mean_lat = math.radians((a[1] + b[1]) / 2.0)
    dx = (a[0] - b[0]) * 111.32 * math.cos(mean_lat)
    dy = (a[1] - b[1]) * 110.574
    return math.hypot(dx, dy)


def split_key(key: str) -> tuple[str, str]:
    parts = key.split("|")
    require(len(parts) == 3, f"Unexpected N02 station key: {key}")
    return parts[0], parts[1]


def build_pool(station_rows: list[dict[str, Any]], network_stations: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Return one record per N02 station key; G2 rows win over browse rows."""
    pool: dict[str, dict[str, Any]] = {}
    for row in station_rows:
        operator, route = split_key(row["n02_station_key"])
        pool.setdefault(row["n02_station_key"], {
            "name": row["display_name_ja"], "operator": operator, "route": route,
            "point": (row["centroid_lon"], row["centroid_lat"]), "group_key": row["n02_station_group_key"],
        })
    for row in network_stations:
        operator, route = split_key(row["sourceStationKey"])
        pool.setdefault(row["sourceStationKey"], {
            "name": row["name"], "operator": operator, "route": route,
            "point": (row["coordinates"][0], row["coordinates"][1]), "group_key": row["sourceStationGroupKey"],
        })
    return pool


def corridor_chains(station_rows: list[dict[str, Any]], crosswalk_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    stations = {row["station_id"]: row for row in station_rows}
    chains: dict[str, list[dict[str, Any]]] = {}
    for row in sorted(crosswalk_rows, key=lambda item: (item["pilot_corridor_id"], item["sequence_index"])):
        station = stations[row["station_id"]]
        chains.setdefault(row["pilot_corridor_id"], []).append({
            "name": station["display_name_ja"],
            "point": (station["centroid_lon"], station["centroid_lat"]),
            "key": station["n02_station_key"],
            "station_id": row["station_id"],
            "station_group_id": row["station_group_id"],
        })
    return chains


def auxiliary_keys(station_rows: list[dict[str, Any]]) -> dict[str, set[str]]:
    keys: dict[str, set[str]] = {}
    for row in station_rows:
        if "auxiliary_context" in row["inclusion_status"]:
            for corridor_id in json.loads(row["pilot_corridor_ids_json"]):
                keys.setdefault(corridor_id, set()).add(row["n02_station_key"])
    return keys


def chain_for(chains: dict[str, list[dict[str, Any]]], corridor_id: str) -> list[dict[str, Any]]:
    chain = chains.get(corridor_id)
    require(chain is not None, f"Missing crosswalk rows for {corridor_id}")
    require(len(chain) >= 2, f"{corridor_id}: segment has fewer than two stations")
    return chain


def best_edge(chain: list[dict[str, Any]], point: tuple[float, float]) -> tuple[float, int] | None:
    best = None
    for index in range(len(chain) - 1):
        a, b = chain[index]["point"], chain[index + 1]["point"]
        direct = approx_km(a, b)
        if direct <= 0:
            continue
        ratio = (approx_km(a, point) + approx_km(point, b)) / direct
        if best is None or ratio < best[0]:
            best = (ratio, index)
    return best


def find_gaps(
    corridors: dict[str, Any],
    chains: dict[str, list[dict[str, Any]]],
    pool: dict[str, dict[str, Any]],
    ratio_max: float,
) -> dict[str, list[dict[str, Any]]]:
    gaps: dict[str, list[dict[str, Any]]] = {}
    for corridor_id, corridor in corridors.items():
        chain = chain_for(chains, corridor_id)
        chain_keys = {item["key"] for item in chain}
        by_name: dict[str, list[tuple[float, float]]] = {}
        for item in chain:
            by_name.setdefault(item["name"], []).append(item["point"])
        routes = set(corridor["source_routes"])
        found = []
        for key, record in sorted(pool.items()):
            if record["operator"] != corridor["operator"] or record["route"] not in routes or key in chain_keys:
                continue
            # Another N02 route record of a segment station (e.g. 横浜 on 根岸線 and 東海道線).
            if any(approx_km(point, record["point"]) <= SAME_STATION_KM for point in by_name.get(record["name"], [])):
                continue
            best = best_edge(chain, record["point"])
            if best is not None and best[0] <= ratio_max:
                index = best[1]
                found.append({
                    "name": record["name"], "source_key": key, "ratio": round(best[0], 3),
                    "after": chain[index]["name"], "before": chain[index + 1]["name"],
                })
        gaps[corridor_id] = found
    return gaps


def check_filters(corridors: dict[str, Any], chains: dict[str, list[dict[str, Any]]], pool: dict[str, dict[str, Any]]) -> None:
    """A filter that matches none of a segment's own records would screen nothing."""
    for corridor_id, corridor in corridors.items():
        overrides = set(corridor.get("source_route_overrides", {}))
        for item in chain_for(chains, corridor_id):
            require(item["key"] in pool, f"{corridor_id}: segment station {item['name']} is missing from the pool")
            if item["name"] in overrides:
                continue
            operator, route = split_key(item["key"])
            require(operator == corridor["operator"] and route in corridor["source_routes"],
                    f"{corridor_id}: screen filter does not match segment station {item['name']} ({item['key']})")


def unscreened_sections(chains: dict[str, list[dict[str, Any]]], polygon: list[list[float]]) -> dict[str, list[list[str]]]:
    """Consecutive runs of segment edges with an endpoint outside the browse polygon."""
    sections: dict[str, list[list[str]]] = {}
    for corridor_id, chain in sorted(chains.items()):
        runs: list[list[str]] = []
        for index in range(len(chain) - 1):
            a, b = chain[index], chain[index + 1]
            if inside(*a["point"], polygon) and inside(*b["point"], polygon):
                continue
            if runs and runs[-1][1] == a["name"]:
                runs[-1][1] = b["name"]
            else:
                runs.append([a["name"], b["name"]])
        if runs:
            sections[corridor_id] = runs
    return sections


def validate_state(correction: dict[str, Any], register_text: str | None) -> str:
    status = correction.get("status")
    require(status in STATUSES, f"Unknown correction status: {status}")
    decision = correction.get("owner_decision")
    if status == "PENDING_OWNER_DECISION":
        require(decision == "PENDING", "owner_decision must stay PENDING until the Owner records a decision")
    else:
        require(isinstance(decision, str) and DECISION_ID.match(decision) is not None,
                f"{status} needs owner_decision set to the accepting DEC/OWNER entry id")
        if register_text is not None:
            require(f"## {decision} " in register_text or f"## {decision}\n" in register_text,
                    f"owner_decision {decision} is not an entry in decisions/DECISION_REGISTER.md")
    if status == "APPLIED":
        confirmation = correction.get("official_confirmation", {})
        records = confirmation.get("records", [])
        require(confirmation.get("status") == "CONFIRMED" and records, "APPLIED needs a CONFIRMED first-hand official check")
        require(all(item.get("url") and item.get("retrieved_at") for item in records), "Each official confirmation needs url and retrieved_at")
        require(correction.get("exclusion_evidence", {}).get("status") == "CONFIRMED", "APPLIED needs confirmed exclusion evidence")
    return status


def validate(
    corridors: dict[str, Any],
    chains: dict[str, list[dict[str, Any]]],
    pool: dict[str, dict[str, Any]],
    correction: dict[str, Any],
    registry_maps: dict[str, dict[str, str]],
    aux_keys: dict[str, set[str]],
    polygon: list[list[float]] | None = None,
    register_text: str | None = None,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[list[str]]]]:
    status = validate_state(correction, register_text)
    detection = correction.get("detection", {})
    ratio_max = detection.get("detour_ratio_max")
    require(isinstance(ratio_max, (int, float)) and RATIO_RANGE[0] <= ratio_max <= RATIO_RANGE[1],
            f"detour_ratio_max must be within {RATIO_RANGE}")
    corrections = correction.get("corrections", {})
    exclusions = correction.get("proposed_exclusions", {})
    require(set(corrections) <= set(corridors), "Correction names an unknown corridor")
    require(set(exclusions) <= set(corridors), "Exclusion names an unknown corridor")
    for corridor_id, corridor in corridors.items():
        aux_names = {pool[key]["name"] for key in aux_keys.get(corridor_id, set())}
        require(aux_names == set(corridor.get("auxiliary_station_names", [])),
                f"{corridor_id}: auxiliary rows differ from auxiliary_station_names")
    check_filters(corridors, chains, pool)
    gaps = find_gaps(corridors, chains, pool, float(ratio_max))

    unscreened: dict[str, list[list[str]]] = {}
    if polygon is not None:
        unscreened = unscreened_sections(chains, polygon)
        expected = {key: [list(span) for span in value] for key, value in detection.get("unscreened_sections", {}).items()}
        require(unscreened == expected, f"Unscreened sections changed; record them in the correction file: {unscreened}")

    for corridor_id in corridors:
        chain = chain_for(chains, corridor_id)
        chain_names = [item["name"] for item in chain]
        spec = corrections.get(corridor_id, {})
        for key in SPEC_KEYS if spec else []:
            require(key in spec, f"{corridor_id}: correction lacks {key}")
        insertions = spec.get("insertions", [])
        for block in insertions:
            require(all(key in block for key in ("after", "before", "stations")), f"{corridor_id}: malformed insertion block")
        inserted = [name for block in insertions for name in block["stations"]]
        source_keys = spec.get("source_keys", {})
        require(sorted(source_keys) == sorted(inserted), f"{corridor_id}: every insertion needs exactly one source key")

        excluded = set()
        for item in exclusions.get(corridor_id, []):
            record = pool.get(item.get("source_key"))
            require(record is not None and record["name"] == item.get("name"), f"{corridor_id}: exclusion {item.get('name')} does not match an N02 record")
            require(bool(item.get("reason")), f"{corridor_id}: exclusion {item['name']} has no reason")
            excluded.add(item["source_key"])

        for name, key in source_keys.items():
            record = pool.get(key)
            require(record is not None and record["name"] == name, f"{corridor_id}: correction key for {name} does not match an N02 record")
            reuse = spec["reuse_ids"].get(name, {})
            require(reuse.get("station_id") is not None and registry_maps["station"].get(key) == reuse["station_id"],
                    f"{corridor_id}: {name} must reuse its DEC-0018 station ID")
            require(registry_maps["station_group"].get(record["group_key"]) == reuse.get("station_group_id"),
                    f"{corridor_id}: {name} must reuse its DEC-0018 station-group ID")

        inserted_keys = set(source_keys.values())
        detected = gaps[corridor_id]
        unexplained = [
            gap for gap in detected
            if gap["source_key"] not in aux_keys.get(corridor_id, set())
            and gap["source_key"] not in excluded
            and not (status in PENDING_STATUSES and gap["source_key"] in inserted_keys)
        ]
        require(not unexplained, f"{corridor_id}: unrecorded missing station(s): " + ", ".join(
            f"{gap['name']} between {gap['after']} and {gap['before']} (ratio {gap['ratio']})" for gap in unexplained
        ))

        if not spec:
            continue
        require(spec["corrected_count"] == spec["locked_count_before"] + len(inserted), f"{corridor_id}: corrected_count arithmetic drift")
        if status in PENDING_STATUSES:
            require(len(chain_names) == spec["locked_count_before"], f"{corridor_id}: segment count no longer matches locked_count_before; update the correction status")
            positions = {gap["source_key"]: (gap["after"], gap["before"]) for gap in detected}
            for block in insertions:
                for name in block["stations"]:
                    require(positions.get(source_keys[name]) == (block["after"], block["before"]),
                            f"{corridor_id}: pending insertion {name} is not detected between {block['after']} and {block['before']}")
        else:
            require(len(chain_names) == spec["corrected_count"], f"{corridor_id}: applied segment count differs from corrected_count")
            for block in insertions:
                require(block["after"] in chain_names, f"{corridor_id}: applied insertion anchor {block['after']} is missing")
                start = chain_names.index(block["after"])
                window = chain_names[start:start + len(block["stations"]) + 2]
                require(window == [block["after"], *block["stations"], block["before"]],
                        f"{corridor_id}: applied insertion is not in official order after {block['after']}")
            by_name = {item["name"]: item for item in chain}
            for name in inserted:
                reuse = spec["reuse_ids"][name]
                entry = by_name[name]
                require(entry["station_id"] == reuse["station_id"] and entry["station_group_id"] == reuse["station_group_id"],
                        f"{corridor_id}: applied {name} did not reuse its DEC-0018 IDs")
    return gaps, unscreened


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--verbose", action="store_true", help="print every screened candidate")
    args = parser.parse_args()
    for path in [RULES, STATIONS, CROSSWALK, NETWORK, NETWORK_REGISTRY, CORRECTION, REGISTER]:
        require(path.exists(), f"Missing {path.relative_to(ROOT)}")
    rules = load_yaml(RULES)
    station_rows = pq.read_table(STATIONS).to_pylist()
    crosswalk_rows = pq.read_table(CROSSWALK).to_pylist()
    network = json.loads(NETWORK.read_text(encoding="utf-8"))
    registry = json.loads(NETWORK_REGISTRY.read_text(encoding="utf-8"))
    correction = load_yaml(CORRECTION)
    corridors = rules["corridors"]
    gaps, unscreened = validate(
        corridors,
        corridor_chains(station_rows, crosswalk_rows),
        build_pool(station_rows, network["stations"]),
        correction,
        registry["maps"],
        auxiliary_keys(station_rows),
        network["scope"]["polygon"],
        REGISTER.read_text(encoding="utf-8"),
    )
    if args.verbose:
        for corridor_id, found in gaps.items():
            for gap in found:
                print(f"  {corridor_id}: {gap['name']} {gap['after']}–{gap['before']} ratio={gap['ratio']}")
    pending = sum(len(block["stations"]) for spec in correction.get("corrections", {}).values() for block in spec.get("insertions", []))
    not_screened = "; ".join(f"{cid} " + ", ".join(f"{a}–{b}" for a, b in spans) for cid, spans in unscreened.items())
    print(
        f"PASS corridor completeness screen (DEC-0018 browse scope only): {len(corridors)} segments, "
        f"no unrecorded missing station in screened sections; {pending} recorded insertion(s) {correction['status']}; "
        f"not screened (outside browse scope): {not_screened or 'none'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
