"""Review candidate predictions against frozen calibration constraints.

This module never reads raw sources, computes scores or approves a model. Input
values and their declared contracts remain unverified candidate submissions.
Holdout, structural and boundary evidence require separate accepted procedures.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re

import yaml


ROOT = Path(__file__).resolve().parents[1]
RELATIONS = {"commercial_mass", "consumer_facing_mass"}
MISSING = {"suppressed", "aggregation_destination", "not_public", "not_surveyed",
           "not_applicable", "source_absent", "outside_scope", "invalid",
           "duplicate_on_other_record", "station_absent"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def load_registry(path):
    raw = Path(path).read_bytes()
    registry = yaml.safe_load(raw)
    require(isinstance(registry, dict), "Registry must be a mapping")
    ids = [c["golden_eval_id"] for c in registry["cases"]]
    require(len(ids) == len(set(ids)) == registry["case_count"], "Registry case count/identity mismatch")
    for split in ("calibration", "holdout"):
        count = sum(c["split"] == split for c in registry["cases"])
        require(count == registry["split_policy"][f"{split}_count"], "Registry split mismatch")
    for key in ("hard_pairwise", "soft_pairwise"):
        for pair in registry[key]:
            require(pair["larger"] in ids and pair["smaller"] in ids, "Unknown pair case")
            require(pair["larger"] != pair["smaller"], "Self-comparison is not valid")
            require(pair["relation"] in RELATIONS, "Unknown metric relation")
    return registry, hashlib.sha256(raw).hexdigest()


def calibration_packet(registry, sha):
    """Allowlist export; mixed calibration/holdout assertions stay excluded."""
    # Free-text constraints can name held-out neighbors even in a calibration
    # case. Do not copy those narratives into a machine-consumed tuning packet.
    fields = ("golden_eval_id", "display_name_ja", "split", "pilot_corridors",
              "structural_tags", "boundary_priority")
    cases = [{key: case[key] for key in fields} for case in registry["cases"]
             if case["split"] == "calibration"]
    ids = {case["golden_eval_id"] for case in cases}
    packet = {
        "registry_sha256": sha,
        "purpose": "calibration_only_candidate_registry_not_ground_truth",
        "cases": cases,
        "structural_assertions": [a for a in registry["hard_structural_assertions"] if set(a["cases"]) <= ids],
    }
    for key in ("hard_pairwise", "soft_pairwise"):
        packet[key] = [{field: p[field] for field in ("larger", "smaller", "relation")}
                       for p in registry[key] if {p["larger"], p["smaller"]} <= ids]
    return packet


def _observation(item):
    require(isinstance(item, dict), "Metric observation must be an object")
    require(set(item) == {"value", "status"}, "Metric observation needs exactly value and status")
    value, status = item["value"], item["status"]
    require(isinstance(status, str), "Observation status must be a string")
    if status in ("observed", "observed_zero"):
        require(type(value) in (int, float) and math.isfinite(value) and value >= 0,
                "Observed activity must be a finite nonnegative number")
        require((value == 0) == (status == "observed_zero"), "Observed zero/status mismatch")
    else:
        require(status in MISSING and value is None, "Unavailable observation must retain a missing status and null")
    return value


def _pair_report(pairs, rows, target):
    results = []
    for index, pair in enumerate(pairs, 1):
        relation = pair["relation"]
        observations = [rows.get(pair[side], {}).get("metrics", {}).get(relation) for side in ("larger", "smaller")]
        values = [None if obs is None else obs["value"] for obs in observations]
        statuses = ["prediction_or_metric_absent" if obs is None else obs["status"] for obs in observations]
        if any(value is None for value in values):
            status = "NOT_EVALUATED"
        else:
            status = "PASS" if values[0] > values[1] else "FAIL"
        results.append({"pair_index": index, **pair, "status": status,
                        "larger_value": values[0], "smaller_value": values[1],
                        "larger_status": statuses[0], "smaller_status": statuses[1]})
    required = len(results)
    passed = sum(r["status"] == "PASS" for r in results)
    failed = sum(r["status"] == "FAIL" for r in results)
    missing = required - passed - failed
    rate = passed / required if required else None
    status = ("NOT_EVALUATED" if not required or missing == required else
              "INCOMPLETE" if missing else "PASS" if rate >= target else "FAIL")
    return {"status": status, "required": required, "evaluated": passed + failed,
            "passed": passed, "failed": failed, "missing": missing,
            "pass_rate": rate, "minimum_pass_rate": target, "results": results}


def evaluate(registry, sha, payload):
    require(isinstance(payload, dict), "Prediction submission must be an object")
    require(payload.get("registry_sha256") == sha, "Registry hash mismatch")
    for key in ("model_run_id", "model_version"):
        require(_text(payload.get(key)), f"Missing {key}")
    require(isinstance(payload.get("model_artifact_sha256"), str) and
            re.fullmatch(r"[a-f0-9]{64}", payload["model_artifact_sha256"]), "Missing/invalid model artifact hash")
    contracts = payload.get("metric_contracts")
    require(isinstance(contracts, dict) and set(contracts) == RELATIONS, "Declare both metric contracts separately")
    for contract in contracts.values():
        require(isinstance(contract, dict), "Metric contract must be an object")
        for key in ("definition", "unit", "reference_period"):
            require(_text(contract.get(key)), f"Metric contract missing {key}")
        refs = contract.get("source_refs")
        require(isinstance(refs, list) and refs and all(_text(ref) for ref in refs), "Metric source references missing")
    packet = calibration_packet(registry, sha)
    allowed = {c["golden_eval_id"] for c in packet["cases"]}
    all_ids = {c["golden_eval_id"] for c in registry["cases"]}
    predictions = payload.get("predictions")
    require(isinstance(predictions, list), "Predictions must be a list")
    rows = {}
    for row in predictions:
        require(isinstance(row, dict), "Prediction must be an object")
        key = row.get("golden_eval_id")
        require(isinstance(key, str) and key in all_ids, "Unknown case ID")
        require(key in allowed, "Holdout predictions are forbidden in the calibration runner")
        require(key not in rows, "Duplicate case prediction")
        require(set(row) == {"golden_eval_id", "metrics"}, "Prediction needs exactly case ID and metrics; do not mix runs or per-row contracts")
        require(isinstance(row["metrics"], dict) and set(row["metrics"]) <= RELATIONS,
                "Use declared mass metrics, not CoreScale or Access substitutes")
        for item in row["metrics"].values():
            _observation(item)
        rows[key] = row
    return {
        "registry_sha256": sha,
        "model_run_id": payload["model_run_id"],
        "model_version": payload["model_version"],
        "model_artifact_sha256": payload["model_artifact_sha256"],
        "metric_contracts": contracts,
        "input_evidence_status": "SUBMITTED_VALUES_AND_CONTRACTS_NOT_INDEPENDENTLY_VERIFIED",
        "evaluation_scope": "calibration_only",
        "coverage": {"required_cases": len(allowed), "provided_cases": len(rows),
                     "missing_case_ids": sorted(allowed - set(rows))},
        "hard_pairwise": _pair_report(packet["hard_pairwise"], rows, 1.0),
        "soft_pairwise": _pair_report(packet["soft_pairwise"], rows, 0.85),
        "structural_assertions": [{"assertion_id": a["assertion_id"], "status": "NOT_EVALUATED"}
                                  for a in registry["hard_structural_assertions"]],
        "acceptance_status": "NOT_EVALUATED",
        "pending_gates": ["verified_input_provenance_and_metric_semantics", "case_to_center_identity",
                          "hard_structural_evidence", "adjudicated_reference_boundaries",
                          "frozen_type_labels_and_separate_holdout_evaluation",
                          "boundary_stability_and_sensitivity"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=ROOT / "data/reference/GOLDEN_EVALS.yml")
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--calibration-packet", action="store_true")
    args = parser.parse_args()
    require(bool(args.predictions) != args.calibration_packet, "Choose predictions or calibration-packet, exclusively")
    inputs = [args.registry] + ([args.predictions] if args.predictions else [])
    require(args.output.resolve() not in {p.resolve() for p in inputs}, "Output must not overwrite an input")
    registry, sha = load_registry(args.registry)
    if args.calibration_packet:
        report = calibration_packet(registry, sha)
    else:
        raw_predictions = args.predictions.read_bytes()
        report = evaluate(registry, sha, json.loads(raw_predictions.decode("utf-8")))
        report["prediction_file_sha256"] = hashlib.sha256(raw_predictions).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")
    if not args.calibration_packet:
        print("Overall model acceptance: NOT_EVALUATED (pairwise subchecks only)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, OSError) as exc:
        raise SystemExit(f"ERROR: {exc}")
