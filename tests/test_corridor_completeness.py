import copy
import json
import unittest
from pathlib import Path

import pyarrow.parquet as pq

from scripts.validate_corridor_completeness import (
    auxiliary_keys,
    best_edge,
    build_pool,
    corridor_chains,
    find_gaps,
    load_yaml,
    unscreened_sections,
    validate,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTER = "## DEC-0099 — accepted correction\n"


def point(name, lat, key, group="g", station_id=None, group_id=None):
    return {"name": name, "point": (139.70, lat), "key": key,
            "station_id": station_id or f"sta_{name}", "station_group_id": group_id or f"stg_{name}"}


def synthetic():
    corridors = {"pc_demo": {"operator": "Op", "source_routes": ["Main"], "auxiliary_station_names": ["Local"]}}
    chains = {"pc_demo": [
        point("A", 35.70, "Op|Main|1"),
        point("C", 35.72, "Op|Main|3"),
        point("D", 35.74, "Op|Main|4"),
    ]}
    pool = {
        "Op|Main|1": {"name": "A", "operator": "Op", "route": "Main", "point": (139.70, 35.70), "group_key": "g1"},
        "Op|Main|2": {"name": "B", "operator": "Op", "route": "Main", "point": (139.7005, 35.71), "group_key": "g2"},
        "Op|Main|3": {"name": "C", "operator": "Op", "route": "Main", "point": (139.70, 35.72), "group_key": "g3"},
        "Op|Main|4": {"name": "D", "operator": "Op", "route": "Main", "point": (139.70, 35.74), "group_key": "g4"},
        "Op|Main|5": {"name": "Local", "operator": "Op", "route": "Main", "point": (139.7003, 35.73), "group_key": "g5"},
        "Op|Branch|6": {"name": "E", "operator": "Op", "route": "Branch", "point": (139.7001, 35.73), "group_key": "g6"},
        "Other|Main|7": {"name": "F", "operator": "Other", "route": "Main", "point": (139.7001, 35.73), "group_key": "g7"},
        "Op|Main|8": {"name": "Far", "operator": "Op", "route": "Main", "point": (139.80, 35.71), "group_key": "g8"},
        "Op|Main|9": {"name": "Beyond", "operator": "Op", "route": "Main", "point": (139.70, 35.76), "group_key": "g9"},
    }
    registry = {"station": {"Op|Main|2": "sta_B"}, "station_group": {"g2": "stg_B", "g9": "stg_other"}}
    aux = {"pc_demo": {"Op|Main|5"}}
    correction = {
        "status": "PENDING_OWNER_DECISION",
        "owner_decision": "PENDING",
        "detection": {"detour_ratio_max": 1.3},
        "corrections": {"pc_demo": {
            "locked_count_before": 3,
            "corrected_count": 4,
            "insertions": [{"after": "A", "before": "C", "stations": ["B"]}],
            "source_keys": {"B": "Op|Main|2"},
            "reuse_ids": {"B": {"station_id": "sta_B", "station_group_id": "stg_B"}},
        }},
        "proposed_exclusions": {},
        "official_confirmation": {"status": "PENDING_FIRST_HAND_CHECK", "records": []},
        "exclusion_evidence": {"status": "PENDING_FIRST_HAND_CHECK", "records": []},
    }
    return corridors, chains, pool, correction, registry, aux


def applied(correction, chains):
    correction["status"] = "APPLIED"
    correction["owner_decision"] = "DEC-0099"
    correction["official_confirmation"] = {"status": "CONFIRMED", "records": [{"url": "https://example.invalid/list", "retrieved_at": "2026-10-01"}]}
    correction["exclusion_evidence"] = {"status": "CONFIRMED", "records": []}
    chains["pc_demo"].insert(1, point("B", 35.71, "Op|Main|2", station_id="sta_B", group_id="stg_B"))


class SyntheticCorridorTest(unittest.TestCase):
    def run_validate(self, corridors, chains, pool, correction, registry, aux, register=REGISTER):
        return validate(corridors, chains, pool, correction, registry, aux, None, register)

    def assertRejected(self, pattern, *parts):
        with self.assertRaisesRegex(AssertionError, pattern):
            self.run_validate(*parts)

    def test_detects_only_between_stations_on_same_operator_route(self):
        corridors, chains, pool, *_ = synthetic()
        gaps = find_gaps(corridors, chains, pool, 1.3)
        self.assertEqual([(g["name"], g["after"], g["before"]) for g in gaps["pc_demo"]], [("B", "A", "C"), ("Local", "C", "D")])

    def test_recorded_pending_insertion_passes(self):
        self.run_validate(*synthetic())

    def test_unrecorded_gap_fails(self):
        parts = synthetic()
        parts[3]["corrections"] = {}
        self.assertRejected("unrecorded missing station", *parts)

    def test_auxiliary_exemption_is_by_key_not_name(self):
        parts = synthetic()
        parts[2]["Op|Main|0"] = {"name": "Local", "operator": "Op", "route": "Main", "point": (139.7003, 35.715), "group_key": "gx"}
        self.assertRejected("unrecorded missing station", *parts)

    def test_pending_exemption_is_by_key_not_name(self):
        parts = synthetic()
        parts[2]["Op|Main|0"] = {"name": "B", "operator": "Op", "route": "Main", "point": (139.7005, 35.73), "group_key": "gx"}
        with self.assertRaises(AssertionError):
            self.run_validate(*parts)

    def test_proposed_exclusion_needs_reason_and_matching_record(self):
        parts = synthetic()
        parts[3]["corrections"] = {}
        parts[3]["proposed_exclusions"] = {"pc_demo": [{"name": "B", "source_key": "Op|Main|2", "reason": "not served"}]}
        self.run_validate(*parts)
        bad = copy.deepcopy(parts[3])
        bad["proposed_exclusions"]["pc_demo"][0]["reason"] = ""
        self.assertRejected("no reason", *parts[:3], bad, *parts[4:])
        bad = copy.deepcopy(parts[3])
        bad["proposed_exclusions"]["pc_demo"][0]["source_key"] = "Op|Main|8"
        self.assertRejected("does not match an N02 record", *parts[:3], bad, *parts[4:])

    def test_unknown_corridors_are_rejected(self):
        parts = synthetic()
        parts[3]["proposed_exclusions"] = {"pc_unknown": []}
        self.assertRejected("Exclusion names an unknown corridor", *parts)
        parts = synthetic()
        parts[3]["corrections"]["pc_unknown"] = {}
        self.assertRejected("Correction names an unknown corridor", *parts)

    def test_new_ids_must_reuse_the_browse_registry(self):
        parts = synthetic()
        parts[3]["corrections"]["pc_demo"]["reuse_ids"]["B"]["station_id"] = "sta_new"
        self.assertRejected("station ID", *parts)
        parts = synthetic()
        parts[3]["corrections"]["pc_demo"]["reuse_ids"]["B"]["station_group_id"] = "stg_other"
        self.assertRejected("station-group ID", *parts)

    def test_correction_key_must_match_its_record(self):
        parts = synthetic()
        parts[3]["corrections"]["pc_demo"]["source_keys"]["B"] = "Op|Main|8"
        self.assertRejected("does not match an N02 record", *parts)
        parts = synthetic()
        parts[3]["corrections"]["pc_demo"]["source_keys"]["Z"] = "Op|Main|8"
        self.assertRejected("exactly one source key", *parts)

    def test_counts_and_positions_are_checked_while_pending(self):
        parts = synthetic()
        parts[3]["corrections"]["pc_demo"]["corrected_count"] = 5
        self.assertRejected("arithmetic", *parts)
        parts = synthetic()
        parts[3]["corrections"]["pc_demo"]["locked_count_before"] = 2
        parts[3]["corrections"]["pc_demo"]["corrected_count"] = 3
        self.assertRejected("locked_count_before", *parts)
        parts = synthetic()
        parts[3]["corrections"]["pc_demo"]["insertions"][0]["after"] = "C"
        parts[3]["corrections"]["pc_demo"]["insertions"][0]["before"] = "D"
        self.assertRejected("not detected between", *parts)

    def test_malformed_correction_is_named(self):
        parts = synthetic()
        del parts[3]["corrections"]["pc_demo"]["locked_count_before"]
        self.assertRejected("lacks locked_count_before", *parts)

    def test_status_and_threshold_are_bounded(self):
        parts = synthetic()
        parts[3]["status"] = "DONE"
        self.assertRejected("Unknown correction status", *parts)
        for value in [1.2, 2.0]:
            parts = synthetic()
            parts[3]["detection"]["detour_ratio_max"] = value
            self.assertRejected("detour_ratio_max", *parts)

    def test_status_cannot_advance_without_an_owner_decision(self):
        parts = synthetic()
        parts[3]["owner_decision"] = "DEC-0099"
        self.assertRejected("must stay PENDING", *parts)
        parts = synthetic()
        parts[3]["status"] = "PENDING_REGENERATION"
        self.assertRejected("owner_decision", *parts)
        parts = synthetic()
        parts[3]["status"] = "PENDING_REGENERATION"
        parts[3]["owner_decision"] = "DEC-0100"
        self.assertRejected("not an entry", *parts)
        parts[3]["owner_decision"] = "DEC-0099"
        self.run_validate(*parts)

    def test_applied_requires_evidence_order_count_and_reused_ids(self):
        corridors, chains, pool, correction, registry, aux = synthetic()
        applied(correction, chains)
        self.run_validate(corridors, chains, pool, correction, registry, aux)

        for mutate, pattern in [
            (lambda c, ch: c["official_confirmation"].__setitem__("status", "PENDING_FIRST_HAND_CHECK"), "first-hand"),
            (lambda c, ch: c["official_confirmation"].__setitem__("records", [{"url": "u"}]), "retrieved_at"),
            (lambda c, ch: c["exclusion_evidence"].__setitem__("status", "PENDING_FIRST_HAND_CHECK"), "exclusion evidence"),
            (lambda c, ch: ch["pc_demo"].__setitem__(1, point("B", 35.71, "Op|Main|2", station_id="sta_new", group_id="stg_B")), "did not reuse"),
            (lambda c, ch: ch["pc_demo"].__setitem__(1, point("B", 35.71, "Op|Main|2", station_id="sta_B", group_id="stg_new")), "did not reuse"),
            (lambda c, ch: c["corrections"]["pc_demo"].update(locked_count_before=4, corrected_count=5), "differs from corrected_count"),
        ]:
            with self.subTest(pattern=pattern):
                corridors, chains, pool, correction, registry, aux = synthetic()
                applied(correction, chains)
                mutate(correction, chains)
                self.assertRejected(pattern, corridors, chains, pool, correction, registry, aux)

        corridors, chains, pool, correction, registry, aux = synthetic()
        applied(correction, chains)
        chains["pc_demo"][1], chains["pc_demo"][2] = chains["pc_demo"][2], chains["pc_demo"][1]
        self.assertRejected("official order", corridors, chains, pool, correction, registry, aux)

    def test_structural_problems_are_named(self):
        parts = synthetic()
        parts[1]["pc_demo"] = parts[1]["pc_demo"][:1]
        self.assertRejected("fewer than two stations", *parts)
        parts = synthetic()
        parts[1].pop("pc_demo")
        self.assertRejected("Missing crosswalk rows", *parts)
        parts = synthetic()
        parts[2].pop("Op|Main|4")
        self.assertRejected("missing from the pool", *parts)
        parts = synthetic()
        del parts[3]["corrections"]["pc_demo"]["insertions"][0]["before"]
        self.assertRejected("malformed insertion block", *parts)

    def test_decision_id_format_is_checked_without_a_register(self):
        parts = synthetic()
        parts[3]["status"] = "PENDING_REGENERATION"
        parts[3]["owner_decision"] = "yes"
        with self.assertRaisesRegex(AssertionError, "owner_decision"):
            validate(*parts, None, None)

    def test_applied_anchor_must_exist(self):
        corridors, chains, pool, correction, registry, aux = synthetic()
        applied(correction, chains)
        correction["corrections"]["pc_demo"]["insertions"][0]["after"] = "Q"
        self.assertRejected("anchor Q is missing", corridors, chains, pool, correction, registry, aux)

    def test_filter_mismatch_is_not_silent(self):
        parts = synthetic()
        parts[0]["pc_demo"]["operator"] = "Renamed"
        self.assertRejected("screen filter does not match", *parts)

    def test_auxiliary_rows_must_match_rules(self):
        parts = synthetic()
        parts[0]["pc_demo"]["auxiliary_station_names"] = []
        self.assertRejected("auxiliary", *parts)

    def test_unscreened_sections_are_reported_and_pinned(self):
        corridors, chains, pool, correction, registry, aux = synthetic()
        polygon = [[139.6, 35.69], [139.8, 35.69], [139.8, 35.73], [139.6, 35.73], [139.6, 35.69]]
        self.assertEqual(unscreened_sections(chains, polygon), {"pc_demo": [["C", "D"]]})
        with self.assertRaisesRegex(AssertionError, "Unscreened sections changed"):
            validate(corridors, chains, pool, correction, registry, aux, polygon, REGISTER)
        correction["detection"]["unscreened_sections"] = {"pc_demo": [["C", "D"]]}
        validate(corridors, chains, pool, correction, registry, aux, polygon, REGISTER)


class CommittedCorridorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = load_yaml(ROOT / "data/reference/PHASE1_IDENTITY_RULES.yml")["corridors"]
        cls.stations = pq.read_table(ROOT / "data/derived/stations.parquet").to_pylist()
        crosswalk = pq.read_table(ROOT / "data/derived/station_line_crosswalk.parquet").to_pylist()
        cls.network = json.loads((ROOT / "dist/network.json").read_text(encoding="utf-8"))
        cls.registry = json.loads((ROOT / "data/reference/NETWORK_IDENTITY_REGISTRY.json").read_text(encoding="utf-8"))["maps"]
        cls.register = (ROOT / "decisions/DECISION_REGISTER.md").read_text(encoding="utf-8")
        cls.chains = corridor_chains(cls.stations, crosswalk)
        cls.pool = build_pool(cls.stations, cls.network["stations"])
        cls.aux = auxiliary_keys(cls.stations)
        cls.polygon = cls.network["scope"]["polygon"]
        cls.correction = load_yaml(ROOT / "data/reference/G2_CORRIDOR_CORRECTION_2026-09-28.yml")

    def run_validate(self, correction):
        return validate(self.rules, self.chains, self.pool, correction, self.registry, self.aux, self.polygon, self.register)

    def test_committed_segments_pass_with_recorded_correction(self):
        _, unscreened = self.run_validate(self.correction)
        self.assertEqual(set(unscreened), {"pc_odakyu_odawara", "pc_tobu_tojo", "pc_tsukuba_express"})

    def test_known_omissions_are_detected_without_the_record(self):
        correction = copy.deepcopy(self.correction)
        correction["corrections"] = {}
        with self.assertRaisesRegex(AssertionError, "pc_jr_sobu_local"):
            self.run_validate(correction)
        gaps = find_gaps(self.rules, self.chains, self.pool, 1.3)
        missing = {g["name"] for cid in ("pc_jr_keihin_tohoku_negishi", "pc_jr_sobu_local") for g in gaps[cid]}
        self.assertTrue({"与野", "北浦和", "西日暮里", "日暮里", "鶯谷", "小岩"} <= missing)

    def test_threshold_sits_between_single_omissions_and_non_service_records(self):
        from scripts.build_public_network import inside

        ratio_max = self.correction["detection"]["detour_ratio_max"]
        worst_single = 0.0
        for chain in self.chains.values():
            for index in range(1, len(chain) - 1):
                trio = chain[index - 1:index + 2]
                if not all(inside(*item["point"], self.polygon) for item in trio):
                    continue
                reduced = [trio[0], trio[2]]
                worst_single = max(worst_single, best_edge(reduced, trio[1]["point"])[0])
        explained = set().union(*self.aux.values())
        for spec in self.correction["corrections"].values():
            explained |= set(spec["source_keys"].values())
        for items in self.correction["proposed_exclusions"].values():
            explained |= {item["source_key"] for item in items}
        wide = find_gaps(self.rules, self.chains, self.pool, 2.0)
        nearest_other = min(g["ratio"] for found in wide.values() for g in found if g["source_key"] not in explained)
        self.assertLess(worst_single, ratio_max)
        self.assertLess(ratio_max, nearest_other)


if __name__ == "__main__":
    unittest.main()
