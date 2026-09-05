#!/usr/bin/env python3
"""Normalize locked Phase 1 G3 inputs without collapsing missingness.

This script is deliberately a *normalization* run.  It does not create a
commercial-center candidate, a score, a ranking, or a public artifact.  Every
numeric field is accompanied by its raw token and observation status where the
source can be missing or suppressed.

The current raw bundle has no legal administrative-boundary polygon.  Therefore
the script records display-prefecture rows and the precisely station-buffered TX
exception, but it does not claim an exact 10 km administrative-boundary clip for
the adjacent-prefecture partitions.  That clip is an explicit later gate.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import io
import json
import math
from pathlib import Path
import struct
import sys
from typing import Any, Iterable
from zipfile import ZipFile

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.observation_semantics import (  # noqa: E402
    ALLOWED_STATUSES,
    NormalizedObservation,
    normalize_census_count,
    normalize_estat_count,
    normalize_s12_count,
)


G3_VERSION = "0.1.0"
DISPLAY_PREFECTURE_CODES = {"11", "12", "13", "14"}
TX_CORRIDOR_ID = "pc_tsukuba_express"
TX_BUFFER_KM = 5.0

# T001163 is the official 500m middle-industry table.  The first 107 variables
# are establishments.  Employee totals begin at T001163108 and the following
# industry values occur in total/male/female triples.  The exact codes below are
# recorded from the official T001163 definition (2021-06-01, 500m, JGD2011).
ECONOMIC_METRIC_COLUMNS = {
    "all_industry_establishments": "T001163001",
    "retail_establishments": "T001163062",  # I2 retail
    "food_establishments": "T001163080",  # M accommodation + food services
    "lifestyle_leisure_establishments": "T001163084",  # N lifestyle + leisure
    "all_industry_employees": "T001163108",
    "retail_employees": "T001163291",
    "food_employees": "T001163345",
    "lifestyle_leisure_employees": "T001163357",
}

# GeoParquet metadata requires an inline PROJJSON object when a CRS is declared.
# This is EPSG:6668 (JGD2011), the datum used by the selected e-Stat mesh tables.
# Source: https://epsg.io/6668.json ; metadata format: GeoParquet 1.1.
JGD2011_PROJJSON = {
    "$schema": "https://proj.org/schemas/v0.7/projjson.schema.json",
    "type": "GeographicCRS",
    "name": "JGD2011",
    "datum": {
        "type": "GeodeticReferenceFrame",
        "name": "Japanese Geodetic Datum 2011",
        "ellipsoid": {
            "name": "GRS 1980",
            "semi_major_axis": 6378137,
            "inverse_flattening": 298.257222101,
        },
    },
    "coordinate_system": {
        "subtype": "ellipsoidal",
        "axis": [
            {"name": "Geodetic latitude", "abbreviation": "Lat", "direction": "north", "unit": "degree"},
            {"name": "Geodetic longitude", "abbreviation": "Lon", "direction": "east", "unit": "degree"},
        ],
    },
    "scope": "Horizontal component of 3D system.",
    "area": "Japan - onshore and offshore.",
    "bbox": {"south_latitude": 17.09, "west_longitude": 122.38, "north_latitude": 46.05, "east_longitude": 157.65},
    "id": {"authority": "EPSG", "code": 6668},
    "remarks": "Replaces JGD2000 (CRS code 4612) with effect from 21st October 2011.",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected mapping in {path}")
    return value


def int_or_none(value: Decimal | None) -> int | None:
    if value is None:
        return None
    if value != value.to_integral_value():
        raise ValueError(f"Expected integral source count, received {value!r}")
    return int(value)


def clean_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def mesh_500m_bounds(mesh_code: str) -> tuple[float, float, float, float]:
    """Return (min_lon, min_lat, max_lon, max_lat) for a fourth-level mesh.

    The formula follows Japan's standard regional mesh code.  e-Stat publishes
    the 500m table keyed by this 9-character fourth-level code; the geometry is
    deterministically reconstructed in JGD2011 geographic coordinates.
    """

    code = str(mesh_code).strip()
    require(len(code) == 9 and code.isdigit(), f"Invalid fourth-level mesh code: {mesh_code!r}")
    quadrant = code[8]
    require(quadrant in {"1", "2", "3", "4"}, f"Invalid 500m mesh quadrant: {mesh_code!r}")

    lat = int(code[:2]) / 1.5
    lon = int(code[2:4]) + 100.0
    lat += int(code[4]) / 12.0
    lon += int(code[5]) / 8.0
    lat += int(code[6]) / 120.0
    lon += int(code[7]) / 80.0
    if quadrant in {"3", "4"}:
        lat += 1.0 / 240.0
    if quadrant in {"2", "4"}:
        lon += 1.0 / 160.0
    return (lon, lat, lon + 1.0 / 160.0, lat + 1.0 / 240.0)


def polygon_wkb(bounds: tuple[float, float, float, float]) -> bytes:
    min_lon, min_lat, max_lon, max_lat = bounds
    points = [
        (min_lon, min_lat),
        (max_lon, min_lat),
        (max_lon, max_lat),
        (min_lon, max_lat),
        (min_lon, min_lat),
    ]
    payload = bytearray(struct.pack("<BI", 1, 3))  # little-endian Polygon
    payload.extend(struct.pack("<I", 1))  # one exterior ring
    payload.extend(struct.pack("<I", len(points)))
    for lon, lat in points:
        payload.extend(struct.pack("<dd", lon, lat))
    return bytes(payload)


def point_wkb(lon: float, lat: float) -> bytes:
    return struct.pack("<BIdd", 1, 1, lon, lat)


def haversine_km(lon_a: float, lat_a: float, lon_b: float, lat_b: float) -> float:
    radius_km = 6371.0088
    lat1, lat2 = math.radians(lat_a), math.radians(lat_b)
    d_lat = lat2 - lat1
    d_lon = math.radians(lon_b - lon_a)
    a = math.sin(d_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(d_lon / 2) ** 2
    return 2 * radius_km * math.asin(math.sqrt(a))


def metric_triplet(prefix: str, observation: NormalizedObservation) -> dict[str, object]:
    return {
        f"{prefix}_raw": observation.raw_value,
        f"{prefix}_value": int_or_none(observation.numeric_value),
        f"{prefix}_status": observation.status,
    }


def read_recovery_events(path: Path) -> dict[str, str]:
    """Return the latest recovered timestamp per artifact from the ignored raw log."""

    events: dict[str, str] = {}
    if not path.is_file():
        return events
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if event.get("result") != "acquired":
            continue
        artifact_id = event.get("artifact_id")
        retrieved_at = event.get("retrieved_at")
        if isinstance(artifact_id, str) and isinstance(retrieved_at, str):
            if retrieved_at > events.get(artifact_id, ""):
                events[artifact_id] = retrieved_at
    return events


def artifact_map(lock: dict[str, Any]) -> dict[str, dict[str, Any]]:
    artifacts = lock.get("artifacts")
    require(isinstance(artifacts, list), "Source lock has no artifact list")
    mapped = {item["artifact_id"]: item for item in artifacts}
    require(len(mapped) == len(artifacts), "Duplicate artifact ids in source lock")
    return mapped


def source_provenance(artifact: dict[str, Any], recovered_at: str | None) -> dict[str, object]:
    return {
        "source_release_id": artifact["source_release_id"],
        "source_artifact_id": artifact["artifact_id"],
        "source_archive_sha256": artifact["sha256"],
        "source_reference_period": str(artifact["reference_date_or_period"]),
        "source_published_at": str(artifact["publication_date_or_period"]),
        "source_lock_retrieved_at": artifact["retrieved_at"],
        "raw_recovered_at": recovered_at,
    }


def tx_station_points() -> list[tuple[float, float]]:
    stations = {
        row["station_id"]: row
        for row in pq.read_table(ROOT / "data/derived/stations.parquet").to_pylist()
    }
    crosswalk = pq.read_table(ROOT / "data/derived/station_line_crosswalk.parquet").to_pylist()
    points = []
    for row in crosswalk:
        if row["pilot_corridor_id"] != TX_CORRIDOR_ID:
            continue
        station = stations[row["station_id"]]
        points.append((float(station["centroid_lon"]), float(station["centroid_lat"])))
    require(points, "No TX station centroids found in confirmed G2 crosswalk")
    return points


def scope_fields(prefecture_partition_code: str, lon: float, lat: float, tx_points: list[tuple[float, float]]) -> dict[str, object]:
    is_display_domain = prefecture_partition_code in DISPLAY_PREFECTURE_CODES
    tx_distance = min(haversine_km(lon, lat, tx_lon, tx_lat) for tx_lon, tx_lat in tx_points)
    is_tx_exception = (
        not is_display_domain
        and prefecture_partition_code == "08"
        and tx_distance <= TX_BUFFER_KM
    )
    if is_display_domain:
        scope_status = "display_domain"
        clip_status = "not_required_display_partition"
    elif is_tx_exception:
        scope_status = "tx_pilot_exception"
        clip_status = "tx_station_buffer_5km"
    else:
        scope_status = "adjacent_partition_untrimmed"
        clip_status = "requires_official_administrative_boundary_clip"
    return {
        "display_scope_status": scope_status,
        "analysis_eligible": is_display_domain or is_tx_exception,
        "tx_5km_exception": is_tx_exception,
        "nearest_tx_station_distance_km": round(tx_distance, 6),
        "administrative_clip_status": clip_status,
    }


def annotate_prefecture_partition_overlap(rows: list[dict[str, object]], source_label: str) -> dict[str, object]:
    """Keep e-Stat prefecture components distinct where one mesh crosses a border.

    e-Stat's own provider-unit note states that a prefecture download contains
    only that prefecture's contribution to a cross-prefecture mesh.  Therefore
    rows sharing a mesh code are not duplicates to discard: they need an
    explicit, scope-aware sum before a whole-mesh surface is made.  G3 preserves
    the components and records that later obligation instead of silently
    choosing one value or summing outside the authorized analysis extent.
    """

    grouped: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(str(row["mesh_code"]), []).append(row)

    multi_partition_meshes = 0
    for mesh_code, members in grouped.items():
        partition_codes = sorted(str(member["prefecture_partition_code"]) for member in members)
        require(
            len(partition_codes) == len(set(partition_codes)),
            f"Duplicate {source_label} mesh record within one prefecture: {mesh_code}",
        )
        is_cross_partition = len(members) > 1
        if is_cross_partition:
            multi_partition_meshes += 1
        rollup_status = (
            "requires_scope_aware_prefecture_component_sum"
            if is_cross_partition
            else "single_prefecture_component"
        )
        for member in members:
            raw_record_key = str(member["source_record_key"])
            pref = str(member["prefecture_partition_code"])
            member["source_raw_record_key"] = raw_record_key
            member["source_record_key"] = f"{source_label}:{pref}:{mesh_code}"
            member["mesh_partition_observation_id"] = f"{source_label}:{pref}:{mesh_code}"
            member["mesh_partition_count"] = len(members)
            member["mesh_partition_codes_json"] = json.dumps(partition_codes, ensure_ascii=False)
            member["cross_partition_rollup_status"] = rollup_status
            member["partition_geometry_status"] = "full_mesh_geometry_not_administrative_partition_clip"

    return {
        "partition_observation_row_count": len(rows),
        "distinct_mesh_count": len(grouped),
        "cross_partition_mesh_count": multi_partition_meshes,
        "cross_partition_component_row_count": sum(
            len(members) for members in grouped.values() if len(members) > 1
        ),
        "rollup_policy": "preserve_prefecture_components_until_scope_aware_sum",
    }


def estat_rows(artifact: dict[str, Any]) -> Iterable[tuple[int, dict[str, str]]]:
    archive_path = ROOT / artifact["local_path"]
    require(archive_path.is_file(), f"Missing raw archive: {archive_path}")
    with ZipFile(archive_path) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(".txt")]
        require(len(members) == 1, f"Expected one text member in {archive_path}, found {members}")
        with archive.open(members[0]) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="cp932", newline=""))
            labels = next(reader, None)
            require(labels is not None and not clean_text(labels.get("KEY_CODE")), f"Missing e-Stat label row: {archive_path}")
            for row_number, row in enumerate(reader, start=3):
                yield row_number, {key: "" if value is None else value for key, value in row.items()}


def check_estat_columns(row: dict[str, str], required: Iterable[str], artifact_id: str) -> None:
    missing = [column for column in required if column not in row]
    require(not missing, f"Missing expected columns in {artifact_id}: {missing}")


def accumulate(summary: dict[str, dict[str, object]], metric: str, observation: NormalizedObservation) -> None:
    entry = summary.setdefault(metric, {"status_counts": {}, "numeric_sum": 0})
    counts = entry["status_counts"]
    assert isinstance(counts, dict)
    counts[observation.status] = int(counts.get(observation.status, 0)) + 1
    if observation.numeric_value is not None:
        entry["numeric_sum"] = int(entry["numeric_sum"]) + int_or_none(observation.numeric_value)


def economic_mesh_rows(
    artifacts: dict[str, dict[str, Any]], recovery_events: dict[str, str], tx_points: list[tuple[float, float]]
) -> tuple[list[dict[str, object]], dict[str, object]]:
    rows: list[dict[str, object]] = []
    summary: dict[str, dict[str, object]] = {}
    selected = sorted(
        (item for item in artifacts.values() if item["source_id"] == "estat_economic_census_mesh_2021"),
        key=lambda item: item["artifact_id"],
    )
    require(len(selected) == 9, "Expected nine locked Economic Census partitions")
    for artifact in selected:
        pref = str(artifact["prefecture_code"]).zfill(2)
        provenance = source_provenance(artifact, recovery_events.get(artifact["artifact_id"]))
        for row_number, raw in estat_rows(artifact):
            check_estat_columns(raw, ["KEY_CODE", *ECONOMIC_METRIC_COLUMNS.values()], artifact["artifact_id"])
            mesh_code = clean_text(raw["KEY_CODE"])
            require(mesh_code is not None, f"Blank mesh code in {artifact['artifact_id']} row {row_number}")
            bounds = mesh_500m_bounds(mesh_code)
            min_lon, min_lat, max_lon, max_lat = bounds
            metrics = {
                name: normalize_estat_count(raw[column])
                for name, column in ECONOMIC_METRIC_COLUMNS.items()
            }
            for name, observation in metrics.items():
                accumulate(summary, name, observation)
            record: dict[str, object] = {
                "mesh_code": mesh_code,
                "prefecture_partition_code": pref,
                "mesh_level": 4,
                "nominal_resolution_m": 500,
                "geometry": polygon_wkb(bounds),
                "geometry_crs": "EPSG:6668",
                "centroid_lon": (min_lon + max_lon) / 2,
                "centroid_lat": (min_lat + max_lat) / 2,
                "source_record_key": mesh_code,
                "source_row_number": row_number,
                "metric_definition_version": "econ-middle-2021-v1",
                **provenance,
                **scope_fields(pref, (min_lon + max_lon) / 2, (min_lat + max_lat) / 2, tx_points),
            }
            for name, observation in metrics.items():
                record.update(metric_triplet(name, observation))
            rows.append(record)
    return rows, {**annotate_prefecture_partition_overlap(rows, "economic-2021"), "metrics": summary}


def population_mesh_rows(
    artifacts: dict[str, dict[str, Any]], recovery_events: dict[str, str], tx_points: list[tuple[float, float]]
) -> tuple[list[dict[str, object]], dict[str, object]]:
    rows: list[dict[str, object]] = []
    summary: dict[str, dict[str, object]] = {}
    selected = sorted(
        (item for item in artifacts.values() if item["source_id"] == "estat_population_census_mesh_2020"),
        key=lambda item: item["artifact_id"],
    )
    require(len(selected) == 9, "Expected nine locked Population Census partitions")
    for artifact in selected:
        pref = str(artifact["prefecture_code"]).zfill(2)
        provenance = source_provenance(artifact, recovery_events.get(artifact["artifact_id"]))
        for row_number, raw in estat_rows(artifact):
            check_estat_columns(raw, ["KEY_CODE", "HTKSYORI", "HTKSAKI", "GASSAN", "T001141001"], artifact["artifact_id"])
            mesh_code = clean_text(raw["KEY_CODE"])
            require(mesh_code is not None, f"Blank mesh code in {artifact['artifact_id']} row {row_number}")
            processing_code = clean_text(raw["HTKSYORI"])
            require(processing_code is not None, f"Blank HTKSYORI in {artifact['artifact_id']} row {row_number}")
            observation = normalize_census_count(raw["T001141001"], suppression_processing_code=processing_code)
            accumulate(summary, "resident_population", observation)
            bounds = mesh_500m_bounds(mesh_code)
            min_lon, min_lat, max_lon, max_lat = bounds
            record: dict[str, object] = {
                "mesh_code": mesh_code,
                "prefecture_partition_code": pref,
                "mesh_level": 4,
                "nominal_resolution_m": 500,
                "geometry": polygon_wkb(bounds),
                "geometry_crs": "EPSG:6668",
                "centroid_lon": (min_lon + max_lon) / 2,
                "centroid_lat": (min_lat + max_lat) / 2,
                "source_record_key": mesh_code,
                "source_row_number": row_number,
                "suppression_processing_code": processing_code,
                "aggregation_destination_mesh_code": clean_text(raw["HTKSAKI"]),
                "aggregated_source_mesh_codes": clean_text(raw["GASSAN"]),
                "metric_definition_version": "population-2020-v1",
                **provenance,
                **scope_fields(pref, (min_lon + max_lon) / 2, (min_lat + max_lat) / 2, tx_points),
                **metric_triplet("resident_population", observation),
            }
            rows.append(record)
    return rows, {**annotate_prefecture_partition_overlap(rows, "population-2020"), "metrics": summary}


def station_access_rows(
    artifacts: dict[str, dict[str, Any]], recovery_events: dict[str, str]
) -> tuple[list[dict[str, object]], dict[str, object]]:
    artifact = artifacts.get("s12-25-gml")
    require(artifact is not None, "Missing locked S12-25 artifact")
    provenance = source_provenance(artifact, recovery_events.get("s12-25-gml"))
    crosswalk = pq.read_table(ROOT / "data/derived/station_line_crosswalk.parquet").to_pylist()
    by_source_key: dict[str, list[dict[str, object]]] = {}
    for row in crosswalk:
        by_source_key.setdefault(row["n02_station_key"], []).append(row)
    archive_path = ROOT / artifact["local_path"]
    with ZipFile(archive_path) as archive:
        member = "S12-25_GML/UTF-8/S12-25_NumberOfPassengers.geojson"
        require(member in archive.namelist(), f"Missing UTF-8 S12 GeoJSON: {archive_path}")
        features = json.loads(archive.read(member))["features"]

    rows: list[dict[str, object]] = []
    seen_source_keys: set[str] = set()
    source_feature_ordinal: dict[str, int] = {}
    summary: dict[str, dict[str, object]] = {}
    for feature_index, feature in enumerate(features, start=1):
        properties = feature.get("properties") or {}
        source_key = "|".join(
            str(properties.get(field, ""))
            for field in ("S12_002", "S12_003", "S12_001c")
        )
        targets = by_source_key.get(source_key)
        if not targets:
            continue
        seen_source_keys.add(source_key)
        source_feature_ordinal[source_key] = source_feature_ordinal.get(source_key, 0) + 1
        existence_code = clean_text(properties.get("S12_059"))
        duplicate_code = clean_text(properties.get("S12_058"))
        require(existence_code is not None and duplicate_code is not None, f"Missing S12 codes for {source_key}")
        observation = normalize_s12_count(
            properties.get("S12_061"),
            existence_code=existence_code,
            duplicate_code=duplicate_code,
        )
        accumulate(summary, "daily_ridership", observation)
        for target in targets:
            rows.append(
                {
                    "station_id": target["station_id"],
                    "station_group_id": target["station_group_id"],
                    "hub_id": target["hub_id"],
                    "line_id": target["line_id"],
                    "pilot_corridor_id": target["pilot_corridor_id"],
                    "sequence_index": target["sequence_index"],
                    "station_line_key": f"{target['station_id']}|{target['line_id']}",
                    "metric_code": "daily_ridership",
                    "allowed_score_domain": "access",
                    "unit": "persons_per_day",
                    "numeric_value": int_or_none(observation.numeric_value),
                    "raw_value": observation.raw_value,
                    "observation_status": observation.status,
                    "s12_source_key": source_key,
                    "source_record_key": f"{source_key}|feature={source_feature_ordinal[source_key]}",
                    "source_feature_index": feature_index,
                    "s12_station_name": clean_text(properties.get("S12_001")),
                    "s12_station_group_code": clean_text(properties.get("S12_001g")),
                    "s12_duplicate_code": duplicate_code,
                    "s12_existence_code": existence_code,
                    "s12_note": clean_text(properties.get("S12_060")),
                    "source_geometry_type": (feature.get("geometry") or {}).get("type"),
                    **provenance,
                }
            )
    missing = sorted(set(by_source_key) - seen_source_keys)
    require(not missing, f"Confirmed G2 crosswalk keys absent from S12: {missing[:10]}")
    return rows, {
        "row_count": len(rows),
        "matched_crosswalk_rows": len(crosswalk),
        "matched_s12_source_keys": len(seen_source_keys),
        "metrics": summary,
    }


def land_price_rows(
    artifacts: dict[str, dict[str, Any]], recovery_events: dict[str, str]
) -> tuple[list[dict[str, object]], dict[str, object]]:
    selected = sorted(
        (item for item in artifacts.values() if item["source_id"] == "ksj_l01_2026"),
        key=lambda item: item["artifact_id"],
    )
    require(len(selected) == 4, "Expected four locked L01 prefectural archives")
    rows: list[dict[str, object]] = []
    seen_keys: set[str] = set()
    summary: dict[str, dict[str, object]] = {}
    for artifact in selected:
        pref = artifact["artifact_id"].split("-")[2]
        archive_path = ROOT / artifact["local_path"]
        geojson_member = f"L01-26_{pref}_GML/L01-26_{pref}.geojson"
        with ZipFile(archive_path) as archive:
            require(geojson_member in archive.namelist(), f"Missing L01 GeoJSON: {archive_path}")
            features = json.loads(archive.read(geojson_member))["features"]
        provenance = source_provenance(artifact, recovery_events.get(artifact["artifact_id"]))
        for feature_index, feature in enumerate(features, start=1):
            props = feature.get("properties") or {}
            geometry = feature.get("geometry") or {}
            require(geometry.get("type") == "Point", f"Non-point L01 geometry in {artifact['artifact_id']}")
            lon, lat = geometry.get("coordinates", [None, None])
            require(isinstance(lon, (int, float)) and isinstance(lat, (int, float)), f"Invalid L01 coordinates in {artifact['artifact_id']}")
            land_key = "-".join(
                str(props.get(field, ""))
                for field in ("L01_001", "L01_002", "L01_003")
            )
            require(land_key not in seen_keys, f"Duplicate L01 standard-land code: {land_key}")
            seen_keys.add(land_key)
            observation = normalize_estat_count(props.get("L01_008"))
            accumulate(summary, "commercial_land_price", observation)
            rows.append(
                {
                    "land_point_source_key": land_key,
                    "source_record_key": land_key,
                    "source_feature_index": feature_index,
                    "prefecture_partition_code": pref,
                    "standard_land_administrative_area_code": clean_text(props.get("L01_001")),
                    "standard_land_index_number": clean_text(props.get("L01_002")),
                    "standard_land_sequence_number": clean_text(props.get("L01_003")),
                    "geometry": point_wkb(float(lon), float(lat)),
                    "geometry_crs": "EPSG:6668",
                    "longitude": float(lon),
                    "latitude": float(lat),
                    "metric_code": "commercial_land_price",
                    "allowed_score_domain": "validation",
                    "unit": "yen_per_m2",
                    "numeric_value": int_or_none(observation.numeric_value),
                    "raw_value": observation.raw_value,
                    "observation_status": observation.status,
                    "current_use": clean_text(props.get("L01_028")),
                    "usage_description": clean_text(props.get("L01_029")),
                    "location": clean_text(props.get("L01_025")),
                    "address": clean_text(props.get("L01_026")),
                    "nearest_station_name": clean_text(props.get("L01_048")),
                    "distance_to_nearest_station_m": props.get("L01_050"),
                    "zoning": clean_text(props.get("L01_051")),
                    "area_m2": props.get("L01_027"),
                    **provenance,
                }
            )
    return rows, {"row_count": len(rows), "metrics": summary}


def geo_metadata(geometry_types: list[str]) -> dict[bytes, bytes]:
    return {
        b"geo": json.dumps(
            {
                "version": "1.1.0",
                "primary_column": "geometry",
                "columns": {
                    "geometry": {
                        "encoding": "WKB",
                        "geometry_types": geometry_types,
                        "crs": JGD2011_PROJJSON,
                    }
                },
            },
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")
    }


def write_parquet(
    path: Path,
    rows: list[dict[str, object]],
    geometry_types: list[str] | None,
) -> dict[str, object]:
    require(rows, f"Refusing to write empty derived artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(rows)
    if geometry_types is not None:
        table = table.replace_schema_metadata(geo_metadata(geometry_types))
    temporary = path.with_suffix(path.suffix + ".part")
    pq.write_table(table, temporary, compression="zstd")
    temporary.replace(path)
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "row_count": table.num_rows,
        "columns": table.column_names,
        "sha256": sha256_file(path),
        "byte_size": path.stat().st_size,
    }


def write_yaml(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    with temporary.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(value, handle, allow_unicode=True, sort_keys=False)
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, default=ROOT / "data/manifests/source_lock.phase1.yml")
    parser.add_argument("--report", type=Path, default=ROOT / "data/qa/g3_normalization_report.yml")
    args = parser.parse_args()
    lock_path = args.lock if args.lock.is_absolute() else ROOT / args.lock
    report_path = args.report if args.report.is_absolute() else ROOT / args.report
    lock = load_yaml(lock_path)
    require(lock.get("gate") == "G1", "G3 requires the accepted G1 source lock")
    artifacts = artifact_map(lock)
    recovery_events = read_recovery_events(ROOT / "data/raw/phase1/acquisition_events.jsonl")
    require(len(recovery_events) >= len(artifacts), "Missing G3 raw-recovery event metadata")
    tx_points = tx_station_points()

    economic_rows, economic_summary = economic_mesh_rows(artifacts, recovery_events, tx_points)
    population_rows, population_summary = population_mesh_rows(artifacts, recovery_events, tx_points)
    access_rows, access_summary = station_access_rows(artifacts, recovery_events)
    land_rows, land_summary = land_price_rows(artifacts, recovery_events)

    outputs = [
        write_parquet(ROOT / "data/derived/economic_mesh_500m.parquet", economic_rows, ["Polygon"]),
        write_parquet(ROOT / "data/derived/population_mesh_500m.parquet", population_rows, ["Polygon"]),
        write_parquet(ROOT / "data/derived/station_access_observations.parquet", access_rows, None),
        write_parquet(ROOT / "data/derived/land_price_points.parquet", land_rows, ["Point"]),
    ]
    report = {
        "g3_version": G3_VERSION,
        "project_id": "tokyo-rail-town-scale-atlas",
        "generated_at": utc_now(),
        "status": "NORMALIZATION_PASS_WITH_SCOPE_AWARE_MESH_ROLLUP_AND_BOUNDARY_CLIP_PENDING",
        "source_lock": {
            "path": lock_path.relative_to(ROOT).as_posix(),
            "sha256": sha256_file(lock_path),
            "artifact_count": lock["artifact_count"],
            "member_count": lock["member_count"],
        },
        "raw_recovery": {
            "event_log": "data/raw/phase1/acquisition_events.jsonl",
            "recovered_artifact_count": len(recovery_events),
            "earliest_recovered_at": min(recovery_events.values()),
            "latest_recovered_at": max(recovery_events.values()),
            "validation_required": "make verify-locked",
        },
        "scope": {
            "display_prefecture_codes": sorted(DISPLAY_PREFECTURE_CODES),
            "tx_exception": {
                "corridor_id": TX_CORRIDOR_ID,
                "buffer_km": TX_BUFFER_KM,
                "status": "candidate_membership_from_confirmed_station_centroids_full_mesh_clip_pending",
            },
            "prefecture_partition_meshes": {
                "official_rule": "A cross-prefecture mesh has a prefecture-specific component in each prefecture download; whole-mesh values require a component sum.",
                "g3_action": "Components are retained as separate observations; no whole-mesh rollup occurs before the authorized scope clip is available.",
                "official_note_url": "https://www.e-stat.go.jp/pdf/gis/teikyo_mesh_chigai.pdf",
            },
            "administrative_boundary_buffer": {
                "required_km": 10,
                "status": "PENDING_OFFICIAL_BOUNDARY_SOURCE_AUDIT",
                "rule": "Adjacent-prefecture rows remain normalized and explicitly flagged; they are not treated as exact 10km buffer membership.",
            },
        },
        "summaries": {
            "economic_mesh": economic_summary,
            "population_mesh": population_summary,
            "station_access": access_summary,
            "land_price": land_summary,
        },
        "outputs": outputs,
        "guardrails": {
            "unknown_tokens_fail": True,
            "numeric_zero_requires_observed_zero": True,
            "s12_is_access_only": True,
            "l01_is_validation_only": True,
            "scores_rankings_centers_or_ui_generated": False,
        },
    }
    write_yaml(report_path, report)
    print(
        "PASS G3 normalization: "
        f"{economic_summary['partition_observation_row_count']} economic partition observations, "
        f"{population_summary['partition_observation_row_count']} population partition observations, "
        f"{access_summary['row_count']} S12 observations, "
        f"{land_summary['row_count']} L01 points"
    )
    print(f"WROTE {report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
