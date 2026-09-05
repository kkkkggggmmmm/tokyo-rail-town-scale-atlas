import copy
import unittest
from pathlib import Path

from scripts.validate_phase1_g3_1_boundary_gate import load_yaml, validate_payloads


ROOT = Path(__file__).resolve().parents[1]


class G31BoundaryGateTest(unittest.TestCase):
    def setUp(self):
        self.audit = load_yaml(ROOT / "data/reference/G3_1_BOUNDARY_SOURCE_AUDIT.yml")
        self.contract = load_yaml(ROOT / "data/reference/G3_1_SCOPE_ROLLUP_CONTRACT.yml")
        self.scope = load_yaml(ROOT / "data/reference/PHASE1_ACQUISITION_SCOPE.yml")

    def test_current_contract_is_valid_but_not_an_execution_authorization(self):
        validate_payloads(self.audit, self.contract, self.scope)
        self.assertFalse(self.audit["raw_acquisition"]["permitted_now"])
        self.assertEqual(self.contract["status"], "NOT_EXECUTABLE_PENDING_GSI_USE_DETERMINATION")

    def test_partial_component_allocation_is_rejected(self):
        bad = copy.deepcopy(self.contract)
        bad["rollup_policy"]["inclusion_rules"]["partial_component"]["eligibility"] = "area_weighted_allocate"
        with self.assertRaises(AssertionError):
            validate_payloads(self.audit, bad, self.scope)

    def test_n03_cannot_be_added_to_acquisition_scope_while_pending(self):
        bad = copy.deepcopy(self.scope)
        bad["artifacts"].append({"source_id": "ksj_n03_2026"})
        with self.assertRaises(AssertionError):
            validate_payloads(self.audit, self.contract, bad)


if __name__ == "__main__":
    unittest.main()
