#!/usr/bin/env python3
"""Validate the G3.1 boundary-source audit and its intentional stop gate.

This verifier validates the policy/configuration that prevents an unaudited N03
derivative from slipping into the Phase 1 pipeline. It deliberately does not
read N03 or create a scope surface; the current audit has not authorized either
operation.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
AUDIT_STATUS = "BLOCKED_PENDING_GSI_USE_DETERMINATION"
CONTRACT_STATUS = "NOT_EXECUTABLE_PENDING_GSI_USE_DETERMINATION"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    require(isinstance(value, dict), f"Expected YAML mapping: {path}")
    return value


def validate_payloads(audit: dict[str, Any], contract: dict[str, Any], acquisition_scope: dict[str, Any]) -> None:
    require(audit.get("audit_status") == AUDIT_STATUS, "G3.1 must retain the pending-GSI stop status")
    candidate = audit.get("selected_candidate", {})
    require(candidate.get("family") == "N03", "Boundary candidate must be N03")
    require(candidate.get("source_release_id") == "N03-20260101", "N03 release must be explicit")
    require(candidate.get("geometry") == "polygon", "Boundary source must be polygon geometry")
    require(candidate.get("crs") == "JGD2011_geographic_EPSG_6668", "Boundary CRS must be recorded")
    temporal = candidate.get("temporal", {})
    require(temporal.get("reference_date_or_period") == "2026-01-01", "N03 reference date drift")
    require(temporal.get("publication_date_or_period") == "2026-04", "N03 publication period drift")
    require(candidate.get("selection_fields", {}).get("local_government_code") == "N03_007", "N03 component selector drift")

    reuse = audit.get("license_and_reuse", {})
    require(reuse.get("catalog_license", {}).get("name") == "Creative Commons Attribution 4.0 International", "N03 CC BY declaration missing")
    gsi = reuse.get("underlying_gsi_result", {})
    require(gsi.get("use_conditions_resolved") is False, "Cannot mark N03 use resolved without official determination")
    require(gsi.get("determination_status") == "PENDING_OWNER_GSI_PROCEDURE_OR_WRITTEN_CONFIRMATION", "GSI determination state drift")

    acquisition = audit.get("raw_acquisition", {})
    require(acquisition.get("permitted_now") is False, "N03 acquisition cannot precede use-condition resolution")
    forbidden = set(acquisition.get("forbidden_until_resolved", []))
    require("N03-derived mesh component inclusion or rollup output" in forbidden, "Rollup stop is missing")
    require("N03-derived public tile, GeoJSON, or map publication" in forbidden, "Publication stop is missing")
    artifacts = acquisition_scope.get("artifacts", [])
    require(not any(item.get("source_id") == "ksj_n03_2026" for item in artifacts), "N03 was added to raw acquisition before approval")

    require(contract.get("status") == CONTRACT_STATUS, "Scope contract must not be executable yet")
    geometry = contract.get("scope_geometry", {})
    require(geometry.get("source_crs") == "EPSG:6668", "Scope source CRS drift")
    require(geometry.get("working_crs") == "EPSG:6677", "Scope working CRS drift")
    display = geometry.get("display_domain", {})
    require(display.get("prefecture_codes") == ["11", "12", "13", "14"], "Display prefectures drift")
    require(geometry.get("analysis_buffer", {}).get("distance_m") == 10000, "10km buffer drift")
    tx = geometry.get("tx_exception", {})
    require(tx.get("distance_m") == 5000, "TX corridor distance drift")
    require("station_centroid_circles" in tx.get("prohibition", ""), "TX centroid-proxy prohibition missing")

    component = contract.get("component_geometry", {})
    require(component.get("construction") == "full_mesh_polygon_intersection_official_prefecture_polygon", "Component support construction drift")
    policy = contract.get("rollup_policy", {})
    require(policy.get("aggregate_name") == "scope_mesh_aggregate", "Ambiguous full-mesh label reintroduced")
    require("exact_trimmed_component_value" in policy.get("forbidden_names", []), "False precision guard missing")
    partial = policy.get("inclusion_rules", {}).get("partial_component", {})
    require(partial.get("eligibility") == "never_allocate_or_fractionally_scale", "Partial component allocation must remain prohibited")
    statuses = policy.get("status_propagation", {}).get("numeric_sum_allowed_only_when_all_included_component_statuses")
    require(statuses == ["observed", "observed_zero"], "Missingness/suppression guard drift")
    promotion = contract.get("promotion_gate", {})
    require("boundary_source_audit.use_conditions_resolved_is_true" in promotion.get("all_must_hold", []), "Use-condition promotion gate missing")
    require("CoreScale" in promotion.get("prohibited_until_all_hold", []), "CoreScale must remain blocked")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, default=ROOT / "data/reference/G3_1_BOUNDARY_SOURCE_AUDIT.yml")
    parser.add_argument("--contract", type=Path, default=ROOT / "data/reference/G3_1_SCOPE_ROLLUP_CONTRACT.yml")
    parser.add_argument("--acquisition-scope", type=Path, default=ROOT / "data/reference/PHASE1_ACQUISITION_SCOPE.yml")
    args = parser.parse_args()
    paths = [args.audit, args.contract, args.acquisition_scope]
    resolved = [path if path.is_absolute() else ROOT / path for path in paths]
    audit, contract, acquisition_scope = (load_yaml(path) for path in resolved)
    validate_payloads(audit, contract, acquisition_scope)
    print("PASS Phase 1 G3.1 boundary audit: N03 processing remains blocked pending GSI use determination")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
