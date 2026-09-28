import copy
import unittest
from pathlib import Path

from scripts.validate_phase1_g3_1_boundary_gate import (
    load_yaml,
    validate_n03_free_contract,
    validate_payloads,
    validate_public_n03_flags,
)


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
        # The former exact source_id check missed N03 under another id, or named only in
        # a URL, path or member name.
        variants = [
            {"source_id": "ksj_n03_2025"},
            {"source_id": "ksj_n03_20260101"},
            {"source_id": "boundary", "url": "https://nlftp.mlit.go.jp/ksj/gml/data/N03/N03-2026/N03-20260101_GML.zip"},
            {"source_id": "boundary", "local_path": "data/raw/phase1/archives/n03-2026.zip"},
            {"source_id": "boundary", "members": [{"name": "N03-20260101.geojson"}]},
            {"source_id": "boundary", "url": "https://example.invalid/Ｎ０３-2026.zip"},
            {"source_id": "boundary", "url": "https://example.invalid/行政区域_2026.zip"},
        ]
        for artifact in variants:
            with self.subTest(artifact=artifact):
                bad = copy.deepcopy(self.scope)
                bad["artifacts"].append(artifact)
                with self.assertRaisesRegex(AssertionError, "N03"):
                    validate_payloads(self.audit, self.contract, bad)

    def test_protective_notes_do_not_trip_the_n03_check(self):
        good = copy.deepcopy(self.scope)
        good["artifacts"][0]["n03_used"] = False
        good["artifacts"][0]["notes"] = "Station geometry only; N03 is not used."
        validate_payloads(self.audit, self.contract, good, load_yaml(ROOT / "SOURCES.yml"))

    def test_every_acquired_artifact_is_bound_to_an_audited_release(self):
        sources = load_yaml(ROOT / "SOURCES.yml")
        validate_payloads(self.audit, self.contract, self.scope, sources)
        n02 = next(item for item in self.scope["artifacts"] if item["source_id"] == "ksj_n02_2025")
        estat = next(item for item in self.scope["artifacts"] if item.get("table_id") == "T001141")
        cases = [
            ({"source_id": "estat_boundary_polygons", "url": "https://www.e-stat.go.jp/gis"}, "audited SOURCES.yml source"),
            ({**n02, "source_release_id": "A002005212020"}, "not the audited release"),
            ({**n02, "url": "https://www.e-stat.go.jp/gis/statmap-search/data?dlserveyId=A002005212020"}, "not a N02 archive"),
            ({**estat, "table_id": "T001192", "url_template": estat["url_template"].replace("T001141", "T001192")}, "not the audited table"),
        ]
        for artifact, pattern in cases:
            with self.subTest(pattern=pattern):
                bad = copy.deepcopy(self.scope)
                bad["artifacts"].append(artifact)
                with self.assertRaisesRegex(AssertionError, pattern):
                    validate_payloads(self.audit, self.contract, bad, sources)


class PublicN03FlagTest(unittest.TestCase):
    def test_flags_must_exist_and_stay_false(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.yml"
            path.write_text("n03_used: false\n", encoding="utf-8")
            validate_public_n03_flags([path])
            for text in ["n03_used: true\n", "other: 1\n"]:
                path.write_text(text, encoding="utf-8")
                with self.assertRaisesRegex(AssertionError, "n03_used"):
                    validate_public_n03_flags([path])
            with self.assertRaisesRegex(AssertionError, "Missing N03 flag manifest"):
                validate_public_n03_flags([Path(directory) / "absent.yml"])


class N03FreeContractTest(unittest.TestCase):
    def setUp(self):
        self.contract = load_yaml(ROOT / "data/reference/N03_FREE_SCOPE_CONTRACT.yml")

    def test_committed_contract_is_valid_and_not_executable(self):
        validate_n03_free_contract(self.contract)

    def test_weakening_edits_are_rejected(self):
        analysis = lambda c: c["scope_rules"]["analysis_scope"]  # noqa: E731
        edits = [
            lambda c: c.__setitem__("contract_id", "other"),
            lambda c: c.__setitem__("status", "EXECUTABLE"),
            lambda c: c.__setitem__("owner_decision", "PENDING"),
            lambda c: c.__setitem__("requires_decision_amending", []),
            lambda c: c["inputs"].__setitem__("mesh_geometry", "n03_polygon_intersection"),
            lambda c: c["inputs"].__setitem__("prohibited_input_codes", ["n03"]),
            lambda c: c["inputs"].__setitem__("acquired_partitions", ["11", "12", "13", "14"]),
            lambda c: c["inputs"].__setitem__("expected_neighbour_partitions", ["08", "09", "10", "19", "22"]),
            lambda c: c["definitions"].__setitem__("display_partition_codes", ["08", "11", "12", "13", "14"]),
            lambda c: c["definitions"].__setitem__("d_max_method", "fixed_735_m"),
            lambda c: c["scope_rules"]["display_scope"].__setitem__("members", "every component of the group"),
            lambda c: analysis(c)["display_mesh_group"].__setitem__("whole_mesh_guard", "always"),
            lambda c: analysis(c)["adjacent_only_mesh_group"].__setitem__("buffer_m", 110000),
            lambda c: analysis(c)["tx_exception"].__setitem__("buffer_m", 15000),
            lambda c: analysis(c)["tx_exception"].__setitem__("applies_to_partition", "all"),
            lambda c: analysis(c)["tx_exception"].__setitem__("prohibition", ""),
            lambda c: c["scope_rules"]["partial_component"].__setitem__("rule", "area_weighted"),
            lambda c: c["status_rules"].__setitem__("numeric_sum_allowed_only_when_all_included_component_statuses", ["observed", "observed_zero", "suppressed"]),
            lambda c: c["status_rules"].__setitem__("otherwise", "use 0"),
            lambda c: c["status_rules"].__setitem__("missing_row", "fill with 0"),
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
