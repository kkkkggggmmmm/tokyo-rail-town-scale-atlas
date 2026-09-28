#!/usr/bin/env python3
"""Validate the G3.1 boundary-source audit and its intentional stop gate.

This verifier validates the policy/configuration that prevents an N03 derivative
from slipping into the Phase 1 pipeline. The Owner did not adopt N03
(OWNER-2026-09-06-N03), so the audit and contract are kept as protective
historical records. It deliberately does not read N03 or create a scope surface.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
AUDIT_STATUS = "BLOCKED_PENDING_GSI_USE_DETERMINATION"
CONTRACT_STATUS = "NOT_EXECUTABLE_PENDING_GSI_USE_DETERMINATION"
N03_PATTERN = re.compile(r"n03", re.IGNORECASE)
PUBLIC_N03_FLAGS = [
    ROOT / "data/manifests/public_supplements.yml",
    ROOT / "data/reference/quantitative/PUBLIC_MAP_SOURCES.yml",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    require(isinstance(value, dict), f"Expected YAML mapping: {path}")
    return value


def strings_in(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [text for key, item in value.items() for text in [str(key), *strings_in(item)]]
    if isinstance(value, list):
        return [text for item in value for text in strings_in(item)]
    return []


def walk_items(value: Any) -> list[tuple[str, Any]]:
    if isinstance(value, dict):
        return [pair for key, item in value.items() for pair in [(str(key), item), *walk_items(item)]]
    if isinstance(value, list):
        return [pair for item in value for pair in walk_items(item)]
    return []


def n03_like(artifact: Any) -> bool:
    """True when any id, URL, path or nested value of an acquisition entry names N03."""
    return any(N03_PATTERN.search(text) for text in strings_in(artifact))


def validate_acquisition_sources(acquisition_scope: dict[str, Any], sources: dict[str, Any]) -> None:
    """Every acquired artifact must belong to an audited SOURCES.yml source with resolved terms."""
    resolved = {
        item.get("source_id")
        for item in sources.get("sources", [])
        if item.get("license", {}).get("resolved") is True
    }
    for artifact in acquisition_scope.get("artifacts", []):
        require(artifact.get("source_id") in resolved,
                f"Acquisition artifact has no audited SOURCES.yml source with resolved terms: {artifact.get('source_id')}")


def validate_payloads(
    audit: dict[str, Any],
    contract: dict[str, Any],
    acquisition_scope: dict[str, Any],
    sources: dict[str, Any] | None = None,
) -> None:
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
    require(not any(n03_like(item) for item in artifacts), "N03 was added to raw acquisition; the Owner did not adopt N03")
    if sources is not None:
        validate_acquisition_sources(acquisition_scope, sources)

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


N03_FREE_STATUS = "PROPOSED_NOT_EXECUTABLE"


def validate_n03_free_contract(contract: dict[str, Any]) -> None:
    """Pin the invariants of the proposed N03-free (mesh-native) scope contract."""
    require(contract.get("contract_id") == "mesh-native-scope-v1", "N03-free contract id drift")
    require(contract.get("status") == N03_FREE_STATUS, "N03-free contract cannot become executable without an Owner decision, its preconditions and a validator change")
    require(contract.get("owner_decision") == "PENDING", "Owner acceptance must be recorded in DECISION_REGISTER.md, not in the contract")
    inputs = contract.get("inputs", {})
    require(inputs.get("mesh_geometry") == "computed_from_mesh_code_jis_x_0410", "Mesh geometry must come from the mesh code")
    prohibited = " ".join(inputs.get("prohibited_inputs", []))
    for term in ["administrative-boundary polygon", "station-centroid circles", "N03"]:
        require(term in prohibited, f"N03-free contract must prohibit {term}")
    definitions = contract.get("definitions", {})
    require("11" in definitions.get("display_component", "") and "14" in definitions.get("display_component", ""), "Display partitions must stay 11-14")
    require("computed per run" in definitions.get("d_max_m", ""), "Mesh diagonal must be computed per run, not fixed")
    rules = contract.get("scope_rules", {})
    analysis = rules.get("analysis_scope", {})
    require("10000 m - d_max_m" in analysis.get("adjacent_only_mesh_group", {}).get("include_when", ""), "Adjacent-only inner buffer test drift")
    tx = analysis.get("tx_exception", {})
    require("5000 m" in tx.get("include_when", "") and tx.get("display") == "never", "TX exception drift")
    require(tx.get("prohibition") == "station_centroid_circles", "TX centroid-proxy prohibition missing")
    require(rules.get("partial_component", {}).get("rule") == "never_allocate_or_fractionally_scale", "Partial component allocation must remain prohibited")
    status_rules = contract.get("status_rules", {})
    require(status_rules.get("numeric_sum_allowed_only_when_all_included_component_statuses") == ["observed", "observed_zero"], "Missingness guard drift")
    require("never zero" in status_rules.get("otherwise", "") and "never fill 0" in status_rules.get("missing_row", ""), "Null-is-never-zero guard missing")
    fields = set(contract.get("required_output_fields", []))
    for field in ["metric_code", "stat_source_release_id", "source_reference_period", "source_published_at", "component_statuses"]:
        require(field in fields, f"N03-free contract output lacks {field}")
    require(contract.get("publication", {}).get("authorized_by_this_contract") is False, "The scope contract must not authorize publication")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, default=ROOT / "data/reference/G3_1_BOUNDARY_SOURCE_AUDIT.yml")
    parser.add_argument("--contract", type=Path, default=ROOT / "data/reference/G3_1_SCOPE_ROLLUP_CONTRACT.yml")
    parser.add_argument("--acquisition-scope", type=Path, default=ROOT / "data/reference/PHASE1_ACQUISITION_SCOPE.yml")
    parser.add_argument("--sources", type=Path, default=ROOT / "SOURCES.yml")
    args = parser.parse_args()
    paths = [args.audit, args.contract, args.acquisition_scope, args.sources]
    resolved = [path if path.is_absolute() else ROOT / path for path in paths]
    audit, contract, acquisition_scope, sources = (load_yaml(path) for path in resolved)
    validate_payloads(audit, contract, acquisition_scope, sources)
    validate_n03_free_contract(load_yaml(ROOT / "data/reference/N03_FREE_SCOPE_CONTRACT.yml"))
    for path in PUBLIC_N03_FLAGS:
        if path.exists():
            payload = load_yaml(path)
            flags = [value for key, value in walk_items(payload) if key == "n03_used"]
            require(flags and all(value is False for value in flags), f"{path.relative_to(ROOT)} must keep n03_used: false")
    print("PASS Phase 1 G3.1 boundary audit: N03 not adopted or acquired; acquired sources audited; N03-free scope contract only proposed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
