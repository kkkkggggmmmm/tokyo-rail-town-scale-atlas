#!/usr/bin/env python3
"""Validate local Phase 1 G3 normalization artifacts and their safety gates.

G3 outputs are intentionally local/reproducible derivatives and are not checked
into Git.  This verifier is therefore part of ``make verify-g3`` after a raw
recovery and normalization run.  It validates the facts that must remain true
before any scope-aware mesh rollup, candidate extraction, score, or UI work.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
import yaml

ROOT = Path(__file__).resolve().parents[1]

REPORT_STATUS = "NORMALIZATION_PASS_WITH_SCOPE_AWARE_MESH_ROLLUP_AND_BOUNDARY_CLIP_PENDING"
OUTPUTS = {
    "economic_mesh": ROOT / "data/derived/economic_mesh_500m.parquet",
    "population_mesh": ROOT / "data/derived/population_mesh_500m.parquet",
    "station_access": ROOT / "data/derived/station_access_observations.parquet",
    "land_price": ROOT / "data/derived/land_price_points.parquet",
}
ECONOMIC_METRICS = [
    "all_industry_establishments",
    "retail_establishments",
    "food_establishments",
    "lifestyle_leisure_establishments",
    "all_industry_employees",
    "retail_employees",
    "food_employees",
    "lifestyle_leisure_employees",
]
UNAVAILABLE_STATUSES = {
    "suppressed",
    "not_public",
    "not_surveyed",
    "not_applicable",
    "source_absent",
    "duplicate_on_other_record",
    "station_absent",
    "outside_scope",
    "invalid",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    require(isinstance(value, dict), f"Expected YAML mapping: {path}")
    return value


def table(path: Path) -> tuple[list[dict[str, Any]], Any]:
    try:
        parquet = pq.ParquetFile(path)
        return pq.read_table(path).to_pylist(), parquet.schema_arrow
    except Exception as exc:  # pragma: no cover - diagnostic wrapper
        raise AssertionError(f"Cannot read {path.relative_to(ROOT)}: {exc}") from exc


def check_observation(row: dict[str, Any], metric: str) -> None:
    raw = row[f"{metric}_raw"]
    value = row[f"{metric}_value"]
    status = row[f"{metric}_status"]
    require(status in {"observed", "observed_zero", "aggregation_destination", *UNAVAILABLE_STATUSES}, f"Unknown {metric} status: {status}")
    if status == "observed":
        require(value is not None and value > 0, f"Observed {metric} lacks positive numeric value")
    elif status == "observed_zero":
        try:
            raw_is_zero = raw is not None and Decimal(str(raw).strip().replace(",", "")) == 0
        except InvalidOperation:
            raw_is_zero = False
        require(raw_is_zero, f"Observed-zero {metric} lacks a source zero token")
        require(value == 0, f"Observed-zero {metric} is not numeric zero")
    elif status == "aggregation_destination":
        require(value is not None and value >= 0, f"Aggregation destination {metric} lacks a published value")
    elif status in UNAVAILABLE_STATUSES:
        require(value is None, f"Unavailable {metric} must not carry numeric value")


def check_geoparquet(schema: Any, expected_geometry_type: str) -> None:
    metadata = schema.metadata or {}
    require(b"geo" in metadata, "GeoParquet metadata is missing")
    geo = json.loads(metadata[b"geo"])
    column = geo.get("columns", {}).get("geometry", {})
    require(geo.get("primary_column") == "geometry", "Unexpected GeoParquet primary column")
    require(column.get("encoding") == "WKB", "Geometry must use WKB")
    require(column.get("geometry_types") == [expected_geometry_type], "Unexpected geometry type")
    crs = column.get("crs")
    require(isinstance(crs, dict), "GeoParquet CRS must be inline PROJJSON")
    require(crs.get("type") == "GeographicCRS", "Unexpected GeoParquet CRS type")
    require(crs.get("id") == {"authority": "EPSG", "code": 6668}, "Unexpected geometry CRS")


def check_mesh_partitions(rows: list[dict[str, Any]], source_label: str, metric_names: list[str]) -> dict[str, int]:
    ids = [row["mesh_partition_observation_id"] for row in rows]
    require(len(ids) == len(set(ids)), f"{source_label} partition observation ID is not unique")
    by_mesh: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        mesh = row["mesh_code"]
        pref = row["prefecture_partition_code"]
        require(len(mesh) == 9 and str(mesh).isdigit(), f"Invalid mesh code: {mesh}")
        require(str(pref).zfill(2) in {"08", "09", "10", "11", "12", "13", "14", "19", "22"}, f"Unexpected source partition: {pref}")
        require(row["source_raw_record_key"] == mesh, f"Raw mesh key not preserved: {mesh}")
        require(row["source_record_key"] == f"{source_label}:{str(pref).zfill(2)}:{mesh}", f"Bad composite source key: {mesh}")
        require(row["partition_geometry_status"] == "full_mesh_geometry_not_administrative_partition_clip", f"Partition geometry status drift: {mesh}")
        require(row["cross_partition_rollup_status"] in {"single_prefecture_component", "requires_scope_aware_prefecture_component_sum"}, f"Unknown rollup status: {mesh}")
        require(row["source_reference_period"], f"Missing reference period: {mesh}")
        require(row["source_published_at"], f"Missing publication period: {mesh}")
        for metric in metric_names:
            check_observation(row, metric)
        by_mesh[mesh].append(row)

    cross_partition_meshes = 0
    for mesh, members in by_mesh.items():
        pref_codes = sorted(str(member["prefecture_partition_code"]).zfill(2) for member in members)
        require(len(pref_codes) == len(set(pref_codes)), f"Duplicate {source_label} row in one partition: {mesh}")
        expected_status = "requires_scope_aware_prefecture_component_sum" if len(members) > 1 else "single_prefecture_component"
        if len(members) > 1:
            cross_partition_meshes += 1
        for member in members:
            require(member["mesh_partition_count"] == len(members), f"Wrong partition count: {mesh}")
            require(json.loads(member["mesh_partition_codes_json"]) == pref_codes, f"Wrong partition list: {mesh}")
            require(member["cross_partition_rollup_status"] == expected_status, f"Wrong rollup status: {mesh}")
    return {"partition_observation_row_count": len(rows), "distinct_mesh_count": len(by_mesh), "cross_partition_mesh_count": cross_partition_meshes}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=ROOT / "data/qa/g3_normalization_report.yml")
    args = parser.parse_args()
    report_path = args.report if args.report.is_absolute() else ROOT / args.report
    require(report_path.is_file(), f"Missing G3 report: {report_path}")
    for path in OUTPUTS.values():
        require(path.is_file(), f"Missing G3 output: {path}")

    report = read_yaml(report_path)
    require(report.get("status") == REPORT_STATUS, "G3 status must retain scope gates")
    require(report.get("guardrails", {}).get("scores_rankings_centers_or_ui_generated") is False, "G3 generated a prohibited downstream artifact")
    scope = report.get("scope", {})
    require(scope.get("administrative_boundary_buffer", {}).get("status") == "PENDING_OFFICIAL_BOUNDARY_SOURCE_AUDIT", "Boundary-audit gate was removed")
    require(scope.get("prefecture_partition_meshes", {}).get("g3_action") == "Components are retained as separate observations; no whole-mesh rollup occurs before the authorized scope clip is available.", "Cross-prefecture mesh policy drifted")
    require(report.get("source_lock", {}).get("artifact_count") == 24, "Unexpected source-lock artifact count")
    require(report.get("source_lock", {}).get("member_count") == 91, "Unexpected source-lock member count")

    rows: dict[str, list[dict[str, Any]]] = {}
    schemas: dict[str, Any] = {}
    for name, path in OUTPUTS.items():
        rows[name], schemas[name] = table(path)
    check_geoparquet(schemas["economic_mesh"], "Polygon")
    check_geoparquet(schemas["population_mesh"], "Polygon")
    check_geoparquet(schemas["land_price"], "Point")
    require(b"geo" not in (schemas["station_access"].metadata or {}), "Access observations must not claim a geometry")

    economic = check_mesh_partitions(rows["economic_mesh"], "economic-2021", ECONOMIC_METRICS)
    population = check_mesh_partitions(rows["population_mesh"], "population-2020", ["resident_population"])
    for row in rows["population_mesh"]:
        processing = row["suppression_processing_code"]
        status = row["resident_population_status"]
        expected = {"0": {"observed", "observed_zero"}, "1": {"aggregation_destination"}, "2": {"suppressed"}}
        require(processing in expected and status in expected[processing], f"Census suppression semantics drift: {row['mesh_partition_observation_id']}")

    access_keys = set()
    for row in rows["station_access"]:
        key = (row["station_line_key"], row["source_record_key"])
        require(key not in access_keys, f"Duplicate access observation: {key}")
        access_keys.add(key)
        require(row["allowed_score_domain"] == "access", "S12 leaked outside Access domain")
        check_observation({"daily_ridership_raw": row["raw_value"], "daily_ridership_value": row["numeric_value"], "daily_ridership_status": row["observation_status"]}, "daily_ridership")
    require(len({row["station_line_key"] for row in rows["station_access"]}) == 233, "Every G2 crosswalk row must have an S12 observation")

    price_keys = [row["land_point_source_key"] for row in rows["land_price"]]
    require(len(price_keys) == len(set(price_keys)), "L01 standard-land key is not unique")
    for row in rows["land_price"]:
        require(row["allowed_score_domain"] == "validation", "L01 leaked into CoreScale")
        check_observation({"commercial_land_price_raw": row["raw_value"], "commercial_land_price_value": row["numeric_value"], "commercial_land_price_status": row["observation_status"]}, "commercial_land_price")

    expected_output_rows = {item["path"]: item for item in report.get("outputs", [])}
    for name, path in OUTPUTS.items():
        key = path.relative_to(ROOT).as_posix()
        expected_output = expected_output_rows.get(key)
        require(expected_output is not None, f"Report does not include output: {key}")
        require(expected_output["row_count"] == len(rows[name]), f"Report row count mismatch: {key}")
        require(expected_output["sha256"] == sha256(path), f"Report hash mismatch: {key}")

    summaries = report.get("summaries", {})
    for name, actual in (("economic_mesh", economic), ("population_mesh", population)):
        recorded = summaries.get(name, {})
        for key, value in actual.items():
            require(recorded.get(key) == value, f"{name} report mismatch: {key}")

    print(
        "PASS Phase 1 G3 normalization: "
        f"{economic['partition_observation_row_count']} economic and "
        f"{population['partition_observation_row_count']} population partition observations; "
        f"{len(rows['station_access'])} access observations; {len(rows['land_price'])} L01 points"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
