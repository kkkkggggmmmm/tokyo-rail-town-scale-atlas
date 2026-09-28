"""Check that partial Golden Eval evidence cannot be reported as acceptance."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.golden_eval import calibration_packet, evaluate, load_registry


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data/reference/GOLDEN_EVALS.yml"
RELATIONS = ("commercial_mass", "consumer_facing_mass")


class GoldenEvalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry, cls.registry_sha = load_registry(REGISTRY_PATH)

    def payload(self):
        """Use artificial values satisfying the current declared comparisons."""
        calibration_ids = [
            row["golden_eval_id"]
            for row in self.registry["cases"]
            if row["split"] == "calibration"
        ]
        metrics = {
            key: {
                relation: {"value": 1.0, "status": "observed"}
                for relation in RELATIONS
            }
            for key in calibration_ids
        }
        for tier in ("hard_pairwise", "soft_pairwise"):
            for pair in self.registry[tier]:
                metrics[pair["larger"]][pair["relation"]]["value"] = 10.0
        return {
            "registry_sha256": self.registry_sha,
            "model_run_id": "synthetic-eval-fixture",
            "model_version": "synthetic-fixture/1",
            "model_artifact_sha256": "a" * 64,
            "metric_contracts": {
                relation: {
                    "definition": "Synthetic comparison fixture; not measured street activity",
                    "unit": "fixture_units",
                    "reference_period": "synthetic-no-observation-year",
                    "source_refs": ["synthetic:golden-eval-test"],
                }
                for relation in RELATIONS
            },
            "predictions": [
                {"golden_eval_id": key, "metrics": metrics[key]}
                for key in calibration_ids
            ],
        }

    def metric(self, payload, key, relation="commercial_mass"):
        return next(
            row["metrics"][relation]
            for row in payload["predictions"]
            if row["golden_eval_id"] == key
        )

    def test_registry_pin_binds_exact_bytes(self):
        raw = REGISTRY_PATH.read_bytes()
        self.assertEqual(self.registry_sha, hashlib.sha256(raw).hexdigest())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registry.yml"
            path.write_bytes(raw + b"\n")
            registry, pin = load_registry(path)
        self.assertEqual(registry, self.registry)
        self.assertNotEqual(pin, self.registry_sha)

    def test_calibration_export_excludes_entire_mixed_holdout_assertions(self):
        packet = calibration_packet(self.registry, self.registry_sha)
        self.assertEqual(len(packet["cases"]), 45)
        self.assertEqual(
            {row["golden_eval_id"] for row in packet["cases"]},
            {f"GE{index:03d}" for index in range(1, 46)},
        )
        self.assertEqual(
            {row["assertion_id"] for row in packet["structural_assertions"]},
            {"HSA01", "HSA02", "HSA03", "HSA04", "HSA08"},
        )
        serialized = json.dumps(packet, ensure_ascii=False)
        for row in packet["cases"]:
            self.assertNotIn("expected_constraints", row)
        self.assertNotIn("原宿—表参道", serialized)
        for row in self.registry["cases"]:
            if row["split"] == "holdout":
                self.assertNotIn(row["golden_eval_id"], serialized)
                # Exact tokens: the held-out 柏 case must not falsely reject
                # the legitimate calibration case 柏の葉キャンパス.
                self.assertNotIn(json.dumps(row["display_name_ja"], ensure_ascii=False), serialized)

    def test_all_pairwise_passes_do_not_imply_model_acceptance(self):
        report = evaluate(self.registry, self.registry_sha, self.payload())
        for tier in ("hard_pairwise", "soft_pairwise"):
            with self.subTest(tier=tier):
                self.assertEqual(report[tier]["required"], 12)
                self.assertEqual(report[tier]["evaluated"], 12)
                self.assertEqual(report[tier]["passed"], 12)
                self.assertEqual(report[tier]["failed"], 0)
                self.assertEqual(report[tier]["missing"], 0)
                self.assertEqual(report[tier]["pass_rate"], 1.0)
                self.assertEqual(len(report[tier]["results"]), 12)
        self.assertEqual(report["coverage"]["required_cases"], 45)
        self.assertEqual(report["coverage"]["provided_cases"], 45)
        self.assertEqual(report["coverage"]["missing_case_ids"], [])
        self.assertEqual(report["acceptance_status"], "NOT_EVALUATED")
        self.assertTrue(report["pending_gates"])
        self.assertEqual(len(report["structural_assertions"]), 8)
        self.assertTrue(all(
            row["status"] == "NOT_EVALUATED" for row in report["structural_assertions"]
        ))

    def test_prediction_order_does_not_change_report_or_mutate_input(self):
        payload = self.payload()
        original = deepcopy(payload)
        baseline = evaluate(self.registry, self.registry_sha, payload)
        self.assertEqual(payload, original)
        payload["predictions"].reverse()
        self.assertEqual(evaluate(self.registry, self.registry_sha, payload), baseline)

    def test_tied_hard_comparison_fails(self):
        payload = self.payload()
        self.metric(payload, "GE002")["value"] = 1.0
        report = evaluate(self.registry, self.registry_sha, payload)["hard_pairwise"]
        self.assertEqual(report["evaluated"], 12)
        self.assertEqual(report["passed"], 11)
        self.assertEqual(report["failed"], 1)
        self.assertNotEqual(report["status"], "PASS")

    def test_soft_denominator_and_eighty_five_percent_cutoff(self):
        payload = self.payload()
        self.metric(payload, "GE006")["value"] = 1.0
        once = evaluate(self.registry, self.registry_sha, payload)["soft_pairwise"]
        self.assertEqual(once["passed"], 11)
        self.assertAlmostEqual(once["pass_rate"], 11 / 12)
        self.metric(payload, "GE013")["value"] = 1.0
        twice = evaluate(self.registry, self.registry_sha, payload)["soft_pairwise"]
        self.assertEqual(twice["passed"], 10)
        self.assertAlmostEqual(twice["pass_rate"], 10 / 12)
        self.assertNotEqual(twice["status"], "PASS")

    def test_missing_case_remains_in_denominator(self):
        payload = self.payload()
        payload["predictions"] = [
            row for row in payload["predictions"] if row["golden_eval_id"] != "GE002"
        ]
        report = evaluate(self.registry, self.registry_sha, payload)
        hard = report["hard_pairwise"]
        self.assertEqual((hard["evaluated"], hard["passed"], hard["missing"]), (11, 11, 1))
        self.assertAlmostEqual(hard["pass_rate"], 11 / 12)
        self.assertEqual(report["coverage"]["missing_case_ids"], ["GE002"])
        self.assertNotEqual(hard["status"], "PASS")

    def test_present_case_with_missing_metric_is_still_unevaluated(self):
        payload = self.payload()
        row = next(row for row in payload["predictions"] if row["golden_eval_id"] == "GE002")
        del row["metrics"]["commercial_mass"]
        report = evaluate(self.registry, self.registry_sha, payload)
        self.assertEqual(report["coverage"]["provided_cases"], 45)
        self.assertEqual(report["hard_pairwise"]["missing"], 1)
        self.assertEqual(report["hard_pairwise"]["evaluated"], 11)
        self.assertNotEqual(report["hard_pairwise"]["status"], "PASS")

    def test_empty_predictions_are_unevaluated_not_vacuously_successful(self):
        payload = self.payload()
        payload["predictions"] = []
        report = evaluate(self.registry, self.registry_sha, payload)
        for tier in ("hard_pairwise", "soft_pairwise"):
            self.assertEqual(report[tier]["evaluated"], 0)
            self.assertEqual(report[tier]["passed"], 0)
            self.assertEqual(report[tier]["missing"], 12)
            self.assertNotEqual(report[tier]["status"], "PASS")
        self.assertEqual(report["coverage"]["provided_cases"], 0)
        self.assertEqual(len(report["coverage"]["missing_case_ids"]), 45)
        self.assertEqual(report["acceptance_status"], "NOT_EVALUATED")

    def test_zero_is_evaluated_but_suppressed_is_not(self):
        zero = self.payload()
        self.metric(zero, "GE002").update(value=0, status="observed_zero")
        suppressed = deepcopy(zero)
        self.metric(suppressed, "GE002").update(value=None, status="suppressed")
        zero_hard = evaluate(self.registry, self.registry_sha, zero)["hard_pairwise"]
        suppressed_hard = evaluate(self.registry, self.registry_sha, suppressed)["hard_pairwise"]
        self.assertEqual((zero_hard["evaluated"], zero_hard["failed"], zero_hard["missing"]), (12, 1, 0))
        self.assertEqual((suppressed_hard["evaluated"], suppressed_hard["failed"], suppressed_hard["missing"]), (11, 0, 1))

    def test_pin_mismatch_rejected(self):
        payload = self.payload()
        payload["registry_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            evaluate(self.registry, self.registry_sha, payload)

    def test_unknown_duplicate_and_holdout_cases_rejected(self):
        for kind in ("unknown", "duplicate", "holdout"):
            with self.subTest(kind=kind):
                payload = self.payload()
                row = deepcopy(payload["predictions"][0])
                row["golden_eval_id"] = {
                    "unknown": "GE999", "duplicate": "GE001", "holdout": "GE046"
                }[kind]
                payload["predictions"].append(row)
                with self.assertRaises(ValueError):
                    evaluate(self.registry, self.registry_sha, payload)

    def test_invalid_values_and_statuses_rejected_before_comparison(self):
        invalid = [
            (0, "observed"), (1, "observed_zero"), (None, "observed"),
            (0, "suppressed"), (float("nan"), "observed"),
            (float("inf"), "observed"), (-1, "observed"),
            (True, "observed"), ("10", "observed"), (None, "unknown"),
        ]
        for value, status in invalid:
            with self.subTest(value=value, status=status):
                payload = self.payload()
                self.metric(payload, "GE002").update(value=value, status=status)
                with self.assertRaises(ValueError):
                    evaluate(self.registry, self.registry_sha, payload)

    def test_unversioned_or_unpinned_model_rejected(self):
        invalid = [
            ("model_run_id", ""), ("model_version", ""),
            ("model_artifact_sha256", "not-a-hash"),
        ]
        for key, value in invalid:
            with self.subTest(key=key):
                payload = self.payload()
                payload[key] = value
                with self.assertRaises(ValueError):
                    evaluate(self.registry, self.registry_sha, payload)

    def test_uninterpretable_metric_contract_rejected(self):
        for key, value in (("definition", ""), ("unit", ""), ("reference_period", ""), ("source_refs", [])):
            with self.subTest(key=key):
                payload = self.payload()
                payload["metric_contracts"]["commercial_mass"][key] = value
                with self.assertRaises(ValueError):
                    evaluate(self.registry, self.registry_sha, payload)

    def test_access_substitution_and_per_case_contract_changes_rejected(self):
        for kind in ("access_metric", "different_run", "different_period"):
            with self.subTest(kind=kind):
                payload = self.payload()
                row = payload["predictions"][0]
                if kind == "access_metric":
                    row["metrics"]["access_power"] = {"value": 100, "status": "observed"}
                elif kind == "different_run":
                    row["model_run_id"] = "other-model-run"
                else:
                    row["reference_period"] = "other-year"
                with self.assertRaises(ValueError):
                    evaluate(self.registry, self.registry_sha, payload)


if __name__ == "__main__":
    unittest.main()
