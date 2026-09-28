#!/usr/bin/env python3
"""Screen the frozen pilot segments for missing N02 route stations.

The G2 identity validator compares each segment with the same hand-written station
list that produced it, so it cannot notice an omitted station. This clone-safe check
uses an independent pool: every N02-25 station record committed for the pilot
(`data/derived/stations.parquet`) and the DEC-0018 metro browse scope
(`dist/network.json`). A record on a corridor's operator and source route that lies
between two consecutive segment stations must be explained as a segment station, an
auxiliary context station, an accepted exclusion, or a recorded pending insertion.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
import yaml


ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "data/reference/PHASE1_IDENTITY_RULES.yml"
STATIONS = ROOT / "data/derived/stations.parquet"
CROSSWALK = ROOT / "data/derived/station_line_crosswalk.parquet"
NETWORK = ROOT / "dist/network.json"
NETWORK_REGISTRY = ROOT / "data/reference/NETWORK_IDENTITY_REGISTRY.json"
CORRECTION = ROOT / "data/reference/G2_CORRIDOR_CORRECTION_2026-09-28.yml"
PENDING_STATUSES = {"PENDING_OWNER_DECISION", "PENDING_REGENERATION"}
STATUSES = PENDING_STATUSES | {"APPLIED"}


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
            "point": (row["centroid_lon"], row["centroid_lat"]),
        })
    for row in network_stations:
        operator, route = split_key(row["sourceStationKey"])
        pool.setdefault(row["sourceStationKey"], {
            "name": row["name"], "operator": operator, "route": route,
            "point": (row["coordinates"][0], row["coordinates"][1]),
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
        })
    return chains


def find_gaps(
    corridors: dict[str, Any],
    chains: dict[str, list[dict[str, Any]]],
    pool: dict[str, dict[str, Any]],
    ratio_max: float,
) -> dict[str, list[dict[str, Any]]]:
    gaps: dict[str, list[dict[str, Any]]] = {}
    for corridor_id, corridor in corridors.items():
        chain = chains.get(corridor_id, [])
        require(len(chain) >= 2, f"{corridor_id}: segment has fewer than two stations")
        names = {item["name"] for item in chain}
        routes = set(corridor["source_routes"])
        found = []
        for key, record in sorted(pool.items()):
            if record["operator"] != corridor["operator"] or record["route"] not in routes or record["name"] in names:
                continue
            best = None
            for index in range(len(chain) - 1):
                a, b = chain[index]["point"], chain[index + 1]["point"]
                direct = approx_km(a, b)
                if direct <= 0:
                    continue
                ratio = (approx_km(a, record["point"]) + approx_km(record["point"], b)) / direct
                if best is None or ratio < best[0]:
                    best = (ratio, index)
            if best is not None and best[0] <= ratio_max:
                index = best[1]
                found.append({
                    "name": record["name"], "source_key": key, "ratio": round(best[0], 3),
                    "after": chain[index]["name"], "before": chain[index + 1]["name"],
                })
        gaps[corridor_id] = found
    return gaps


def validate(
    corridors: dict[str, Any],
    chains: dict[str, list[dict[str, Any]]],
    pool: dict[str, dict[str, Any]],
    correction: dict[str, Any],
    registry_maps: dict[str, dict[str, str]],
) -> dict[str, list[dict[str, Any]]]:
    status = correction.get("status")
    require(status in STATUSES, f"Unknown correction status: {status}")
    ratio_max = correction.get("detection", {}).get("detour_ratio_max")
    require(isinstance(ratio_max, (int, float)) and 1.0 < ratio_max <= 1.5, "Detour ratio threshold must be in (1.0, 1.5]")
    gaps = find_gaps(corridors, chains, pool, float(ratio_max))
    corrections = correction.get("corrections", {})
    exclusions = correction.get("accepted_exclusions", {})
    require(set(corrections) <= set(corridors), "Correction names an unknown corridor")

    for corridor_id, corridor in corridors.items():
        chain_names = [item["name"] for item in chain_for(chains, corridor_id)]
        spec = corrections.get(corridor_id, {})
        insertions = spec.get("insertions", [])
        inserted = [name for block in insertions for name in block["stations"]]
        allowed_context = set(corridor.get("auxiliary_station_names", []))
        excluded = {}
        for item in exclusions.get(corridor_id, []):
            record = pool.get(item["source_key"])
            require(record is not None and record["name"] == item["name"], f"{corridor_id}: exclusion {item['name']} does not match an N02 record")
            require(bool(item.get("reason")), f"{corridor_id}: exclusion {item['name']} has no reason")
            excluded[item["source_key"]] = item["name"]

        for name, key in spec.get("source_keys", {}).items():
            record = pool.get(key)
            require(record is not None and record["name"] == name, f"{corridor_id}: correction key for {name} does not match an N02 record")
            reuse = spec.get("reuse_ids", {}).get(name, {})
            require(registry_maps["station"].get(key) == reuse.get("station_id"), f"{corridor_id}: {name} must reuse its DEC-0018 station ID")
            require(reuse.get("station_group_id") in set(registry_maps["station_group"].values()), f"{corridor_id}: {name} must reuse its DEC-0018 station-group ID")
        require(set(spec.get("source_keys", {})) == set(inserted), f"{corridor_id}: every insertion needs exactly one source key")

        detected = gaps[corridor_id]
        unexplained = [
            gap for gap in detected
            if gap["name"] not in allowed_context
            and gap["source_key"] not in excluded
            and not (status in PENDING_STATUSES and gap["name"] in inserted)
        ]
        require(not unexplained, f"{corridor_id}: unrecorded missing station(s): " + ", ".join(
            f"{gap['name']} between {gap['after']} and {gap['before']} (ratio {gap['ratio']})" for gap in unexplained
        ))

        if not spec:
            continue
        if status in PENDING_STATUSES:
            require(len(chain_names) == spec["locked_count_before"], f"{corridor_id}: segment count no longer matches locked_count_before; update the correction status")
            detected_positions = {gap["name"]: (gap["after"], gap["before"]) for gap in detected}
            for block in insertions:
                for name in block["stations"]:
                    require(detected_positions.get(name) == (block["after"], block["before"]),
                            f"{corridor_id}: pending insertion {name} is not detected between {block['after']} and {block['before']}")
        else:
            for block in insertions:
                require(block["after"] in chain_names, f"{corridor_id}: applied insertion anchor {block['after']} is missing")
                start = chain_names.index(block["after"])
                window = chain_names[start:start + len(block["stations"]) + 2]
                require(window == [block["after"], *block["stations"], block["before"]],
                        f"{corridor_id}: applied insertion is not in official order after {block['after']}")
        require(spec["corrected_count"] == spec["locked_count_before"] + len(inserted), f"{corridor_id}: corrected_count arithmetic drift")
        if status == "APPLIED":
            require(len(chain_names) == spec["corrected_count"], f"{corridor_id}: applied segment count differs from corrected_count")
    return gaps


def chain_for(chains: dict[str, list[dict[str, Any]]], corridor_id: str) -> list[dict[str, Any]]:
    chain = chains.get(corridor_id)
    require(chain is not None, f"Missing crosswalk rows for {corridor_id}")
    return chain


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true", help="print every screened candidate")
    args = parser.parse_args()
    for path in [RULES, STATIONS, CROSSWALK, NETWORK, NETWORK_REGISTRY, CORRECTION]:
        require(path.exists(), f"Missing {path.relative_to(ROOT)}")
    rules = load_yaml(RULES)
    station_rows = pq.read_table(STATIONS).to_pylist()
    crosswalk_rows = pq.read_table(CROSSWALK).to_pylist()
    network = json.loads(NETWORK.read_text(encoding="utf-8"))
    registry = json.loads(NETWORK_REGISTRY.read_text(encoding="utf-8"))
    correction = load_yaml(CORRECTION)
    corridors = rules["corridors"]
    gaps = validate(
        corridors,
        corridor_chains(station_rows, crosswalk_rows),
        build_pool(station_rows, network["stations"]),
        correction,
        registry["maps"],
    )
    if args.verbose:
        for corridor_id, found in gaps.items():
            for gap in found:
                print(f"  {corridor_id}: {gap['name']} {gap['after']}–{gap['before']} ratio={gap['ratio']}")
    pending = sum(len(block["stations"]) for spec in correction.get("corrections", {}).values() for block in spec.get("insertions", []))
    state = f"{pending} recorded insertion(s) {correction['status']}"
    print(f"PASS corridor completeness screen: {len(corridors)} segments, no unrecorded missing stations; {state}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
