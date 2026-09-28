import copy
import unittest
from pathlib import Path

from scripts.validate_phase1_g3_1_boundary_gate import load_yaml, validate_n03_free_contract, validate_payloads


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

    def test_n03_under_another_id_or_only_in_its_url_is_rejected(self):
        # Review probes M02/G1: both passed the former exact-string check.
        variants = [
            {"source_id": "ksj_n03_2025"},
            {"source_id": "ksj_n03_20260101"},
            {"source_id": "boundary", "url": "https://nlftp.mlit.go.jp/ksj/gml/data/N03/N03-2026/N03-20260101_GML.zip"},
            {"source_id": "boundary", "local_path": "data/raw/phase1/archives/n03-2026.zip"},
            {"source_id": "boundary", "members": [{"name": "N03-20260101.geojson"}]},
        ]
        for artifact in variants:
            with self.subTest(artifact=artifact):
                bad = copy.deepcopy(self.scope)
                bad["artifacts"].append(artifact)
                with self.assertRaisesRegex(AssertionError, "N03"):
                    validate_payloads(self.audit, self.contract, bad)

    def test_every_acquired_artifact_needs_an_audited_source(self):
        sources = load_yaml(ROOT / "SOURCES.yml")
        validate_payloads(self.audit, self.contract, self.scope, sources)
        bad = copy.deepcopy(self.scope)
        bad["artifacts"].append({"source_id": "estat_boundary_polygons", "url": "https://www.e-stat.go.jp/gis"})
        with self.assertRaisesRegex(AssertionError, "audited SOURCES.yml source"):
            validate_payloads(self.audit, self.contract, bad, sources)


class N03FreeContractTest(unittest.TestCase):
    def setUp(self):
        self.contract = load_yaml(ROOT / "data/reference/N03_FREE_SCOPE_CONTRACT.yml")

    def test_committed_contract_is_valid_and_not_executable(self):
        validate_n03_free_contract(self.contract)

    def test_weakening_edits_are_rejected(self):
        edits = [
            lambda c: c.__setitem__("status", "EXECUTABLE"),
            lambda c: c.__setitem__("owner_decision", "ACCEPTED"),
            lambda c: c["inputs"].__setitem__("prohibited_inputs", ["N03"]),
            lambda c: c["scope_rules"]["partial_component"].__setitem__("rule", "area_weighted"),
            lambda c: c["status_rules"].__setitem__("numeric_sum_allowed_only_when_all_included_component_statuses", ["observed", "observed_zero", "suppressed"]),
            lambda c: c["status_rules"].__setitem__("missing_row", "fill with 0"),
            lambda c: c["scope_rules"]["analysis_scope"]["tx_exception"].__setitem__("prohibition", ""),
            lambda c: c["definitions"].__setitem__("d_max_m", "735"),
            lambda c: c["publication"].__setitem__("authorized_by_this_contract", True),
            lambda c: c.__setitem__("required_output_fields", ["mesh_code"]),
        ]
        for index, edit in enumerate(edits):
            with self.subTest(edit=index):
                bad = copy.deepcopy(self.contract)
                edit(bad)
                with self.assertRaises(AssertionError):
                    validate_n03_free_contract(bad)


if __name__ == "__main__":
    unittest.main()
