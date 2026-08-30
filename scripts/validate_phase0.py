#!/usr/bin/env python3
"""Validate Phase 0 registries, schema, map, and missingness contract."""

from __future__ import annotations

import csv
import io
from pathlib import Path
import sqlite3
import sys
import unittest
import xml.etree.ElementTree as ET

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.observation_semantics import (
    normalize_census_count,
    normalize_estat_count,
    normalize_s12_count,
)

def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_yaml(relative_path: str):
    path = ROOT / relative_path
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def validate_required_files() -> None:
    required = [
        "AGENTS.md",
        "PROJECT_STATE.md",
        "DATA_DICTIONARY.md",
        "SOURCES.yml",
        "CENTER_MODEL.md",
        "schema/canonical.sql",
        "schema/station_line_crosswalk.schema.yml",
        "data/reference/PILOT_LINES.yml",
        "data/reference/GOLDEN_EVALS.yml",
        "docs/PILOT_SCOPE.md",
        "docs/pilot_scope_map.svg",
        "docs/PHASE0_AUDIT_REPORT.md",
        "docs/OFFICIAL_CORRECTION_RECHECK_2026-08-30.md",
        "docs/PHASE1_EXECUTION_PLAN.md",
    ]
    missing = [item for item in required if not (ROOT / item).is_file()]
    require(not missing, f"Missing required files: {missing}")


def validate_sources() -> None:
    manifest = load_yaml("SOURCES.yml")
    recheck = manifest["official_recheck"]
    require(recheck["checked_at"] == "2026-08-30", "Official recheck date missing")
    require(recheck["raw_archives_verified"] is False, "Phase 0 must not claim raw archive verification")
    sources = manifest["sources"]
    require(len(sources) == 5, "Source manifest must contain exactly five audited families")
    expected_families = {
        "N02",
        "S12",
        "ECONOMIC_CENSUS_MESH",
        "POPULATION_CENSUS_MESH",
        "L01",
    }
    require({source["family"] for source in sources} == expected_families, "Unexpected source families")
    require(manifest["missingness_contract"]["null_is_never_zero"] is True, "NULL/zero contract missing")
    for source in sources:
        require(source["license"]["resolved"] is True, f"Unresolved license: {source['source_id']}")
        temporal = source["temporal"]
        require(temporal.get("reference_date_or_period"), f"Missing reference time: {source['source_id']}")
        require(temporal.get("publication_date_or_period"), f"Missing publication time: {source['source_id']}")
        require("retrieved_at" in temporal, f"Missing retrieval field: {source['source_id']}")
        require(source["artifact_status"] == "not_acquired_phase0", "Phase 0 must not claim data acquisition")
        source_recheck = source["official_recheck"]
        require(source_recheck["checked_at"] == "2026-08-30", f"Missing recheck date: {source['source_id']}")
        require(source_recheck["evidence_urls"], f"Missing recheck evidence: {source['source_id']}")
        require(source_recheck["acquisition_guard"], f"Missing acquisition guard: {source['source_id']}")
    scale_sources = {source["family"] for source in sources if source["model_role"]["core_scale_eligible"]}
    require(scale_sources == {"ECONOMIC_CENSUS_MESH"}, "Only Economic Census may enter CoreScale at Phase 0")
    s12 = next(source for source in sources if source["family"] == "S12")
    require(s12["model_role"]["core_scale_eligible"] is False, "S12 leaked into CoreScale")
    l01 = next(source for source in sources if source["family"] == "L01")
    require(l01["temporal"]["latest_known_correction_date"] == "2026-04-24", "L01 correction date changed")
    require(l01["official_recheck"]["requires_post_correction_archive"] is True, "L01 correction lock missing")
    economic = next(source for source in sources if source["family"] == "ECONOMIC_CENSUS_MESH")
    require(economic["temporal"]["detailed_mesh_distribution_start"] == "2025-01-23", "Economic Census distribution event missing")
    population = next(source for source in sources if source["family"] == "POPULATION_CENSUS_MESH")
    require(population["temporal"]["prefectural_download_distribution_start"] == "2025-10-09", "Census distribution event missing")


def validate_pilot() -> None:
    registry = load_yaml("data/reference/PILOT_LINES.yml")
    corridors = registry["pilot_corridors"]
    require(len(corridors) == 8, "Pilot must contain exactly eight corridors")
    ids = [corridor["pilot_corridor_id"] for corridor in corridors]
    require(len(ids) == len(set(ids)), "Pilot corridor IDs must be unique")
    require(registry["analysis_extent"]["default_boundary_buffer_m"] == 10000, "Analysis buffer changed")
    tx = next(item for item in corridors if item["pilot_corridor_id"] == "pc_tsukuba_express")
    require("08" in tx["prefectures"], "TX pilot exception must include Ibaraki")


def _walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def validate_golden() -> None:
    registry = load_yaml("data/reference/GOLDEN_EVALS.yml")
    cases = registry["cases"]
    require(len(cases) == 60, "Golden Eval registry must contain exactly 60 cases")
    require(registry["case_count"] == len(cases), "Golden case_count does not match cases")
    ids = [case["golden_eval_id"] for case in cases]
    require(len(ids) == len(set(ids)), "Golden Eval IDs must be unique")
    require(ids == [f"GE{index:03d}" for index in range(1, 61)], "Golden Eval IDs must be GE001..GE060")
    split_counts = {
        "calibration": sum(case["split"] == "calibration" for case in cases),
        "holdout": sum(case["split"] == "holdout" for case in cases),
    }
    require(split_counts == {"calibration": 45, "holdout": 15}, f"Bad Golden split: {split_counts}")
    for case in cases:
        require(case.get("structural_tags"), f"Missing structural tags: {case['golden_eval_id']}")
        require(case.get("expected_constraints"), f"Missing constraints: {case['golden_eval_id']}")
    forbidden = {"score", "rank", "final_class"}
    require(not (set(_walk_keys(registry)) & forbidden), "Golden registry contains final output fields")
    require(len(registry["hard_pairwise"]) >= 10, "Too few hard pairwise constraints")
    require(len(registry["soft_pairwise"]) >= 10, "Too few soft pairwise constraints")
    require(registry["hard_structural_assertions"], "Structural assertions missing")


def validate_identity_fixture() -> None:
    fixture = load_yaml("tests/fixtures/identity_cases.yml")
    cases = fixture["cases"]
    required_scenarios = {
        "same_name_nearby_source_seed",
        "different_name_official_transfer",
        "rename_across_releases",
        "ambiguous_proximity",
        "center_split_across_model_runs",
    }
    require({case["scenario"] for case in cases} == required_scenarios, "Identity fixture coverage changed")
    for case in cases:
        require(case.get("expected_action"), f"Missing expected identity action: {case['case_id']}")
        require(case.get("forbidden_action"), f"Missing forbidden identity action: {case['case_id']}")
        require(case.get("rationale"), f"Missing identity rationale: {case['case_id']}")


def validate_schema() -> None:
    sql = (ROOT / "schema/canonical.sql").read_text(encoding="utf-8")
    required_tables = [
        "station",
        "station_group",
        "hub",
        "center",
        "station_center_link",
        "line_center_link",
        "entity_alias",
        "feature_observation",
    ]
    lower_sql = sql.lower()
    for table in required_tables:
        require(f"create table {table} " in lower_sql, f"Required table missing: {table}")
    require("unique (line_id, center_id, model_run_id)" in lower_sql, "Line-center deduplication missing")
    connection = sqlite3.connect(":memory:")
    try:
        connection.executescript(sql)
    finally:
        connection.close()


def validate_map() -> None:
    svg_path = ROOT / "docs/pilot_scope_map.svg"
    root = ET.parse(svg_path).getroot()
    require(root.tag.endswith("svg"), "Pilot map is not valid SVG")
    require(root.attrib.get("viewBox") == "0 0 1200 860", "Unexpected pilot map canvas")


def validate_missingness_fixture() -> None:
    fixture = ROOT / "tests/fixtures/missingness_cases.csv"
    with fixture.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    require(rows, "Missingness fixture is empty")
    for row in rows:
        source = row["source"]
        raw = row["raw_value"]
        if source == "estat":
            result = normalize_estat_count(raw)
        elif source == "s12":
            result = normalize_s12_count(raw, existence_code=row["code_a"], duplicate_code=row["code_b"])
        elif source == "census":
            result = normalize_census_count(raw, suppression_processing_code=row["code_a"])
        else:
            raise AssertionError(f"Unknown fixture source: {source}")
        require(result.status == row["expected_status"], f"Bad status for fixture row: {row}")
        expected_numeric = row["expected_numeric"]
        actual_numeric = "" if result.numeric_value is None else str(result.numeric_value)
        require(actual_numeric == expected_numeric, f"Bad numeric value for fixture row: {row}")


def run_unit_tests() -> None:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py")
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=1).run(suite)
    if not result.wasSuccessful():
        raise AssertionError(stream.getvalue())


def main() -> int:
    checks = [
        ("required files", validate_required_files),
        ("source manifest", validate_sources),
        ("pilot scope", validate_pilot),
        ("golden registry", validate_golden),
        ("identity policy fixture", validate_identity_fixture),
        ("canonical schema", validate_schema),
        ("pilot map", validate_map),
        ("missingness fixture", validate_missingness_fixture),
        ("unit tests", run_unit_tests),
    ]
    for name, function in checks:
        function()
        print(f"PASS  {name}")
    print("PASS  Phase 0 canonical artifact set")
    return 0


if __name__ == "__main__":
    sys.exit(main())
