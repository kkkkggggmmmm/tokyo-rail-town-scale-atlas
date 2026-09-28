import copy
import json
import unittest
from pathlib import Path

import pyarrow.parquet as pq

from scripts.validate_corridor_completeness import (
    build_pool,
    corridor_chains,
    find_gaps,
    load_yaml,
    validate,
)


ROOT = Path(__file__).resolve().parents[1]


def synthetic():
    corridors = {"pc_demo": {"operator": "Op", "source_routes": ["Main"], "auxiliary_station_names": ["Local"]}}
    chains = {"pc_demo": [
        {"name": "A", "point": (139.70, 35.70)},
        {"name": "C", "point": (139.70, 35.72)},
        {"name": "D", "point": (139.70, 35.74)},
    ]}
    pool = {
        "Op|Main|1": {"name": "A", "operator": "Op", "route": "Main", "point": (139.70, 35.70)},
        "Op|Main|2": {"name": "B", "operator": "Op", "route": "Main", "point": (139.7005, 35.71)},
        "Op|Main|3": {"name": "C", "operator": "Op", "route": "Main", "point": (139.70, 35.72)},
        "Op|Main|4": {"name": "D", "operator": "Op", "route": "Main", "point": (139.70, 35.74)},
        "Op|Branch|5": {"name": "E", "operator": "Op", "route": "Branch", "point": (139.7001, 35.73)},
        "Other|Main|6": {"name": "F", "operator": "Other", "route": "Main", "point": (139.7001, 35.73)},
        "Op|Main|7": {"name": "Far", "operator": "Op", "route": "Main", "point": (139.80, 35.71)},
        "Op|Main|8": {"name": "Beyond", "operator": "Op", "route": "Main", "point": (139.70, 35.76)},
    }
    registry = {"station": {"Op|Main|2": "sta_b"}, "station_group": {"g2": "stg_b"}}
    correction = {
        "status": "PENDING_REGENERATION",
        "detection": {"detour_ratio_max": 1.3},
        "corrections": {"pc_demo": {
            "locked_count_before": 3,
            "corrected_count": 4,
            "insertions": [{"after": "A", "before": "C", "stations": ["B"]}],
            "source_keys": {"B": "Op|Main|2"},
            "reuse_ids": {"B": {"station_id": "sta_b", "station_group_id": "stg_b"}},
        }},
        "accepted_exclusions": {},
    }
    return corridors, chains, pool, correction, registry


class SyntheticCorridorTest(unittest.TestCase):
    def test_detects_only_between_stations_on_same_operator_route(self):
        corridors, chains, pool, _, _ = synthetic()
        gaps = find_gaps(corridors, chains, pool, 1.3)
        self.assertEqual([(g["name"], g["after"], g["before"]) for g in gaps["pc_demo"]], [("B", "A", "C")])

    def test_recorded_pending_insertion_passes(self):
        validate(*synthetic())

    def test_unrecorded_gap_fails(self):
        corridors, chains, pool, correction, registry = synthetic()
        correction["corrections"] = {}
        with self.assertRaisesRegex(AssertionError, "unrecorded missing station"):
            validate(corridors, chains, pool, correction, registry)

    def test_accepted_exclusion_needs_reason_and_matching_record(self):
        corridors, chains, pool, correction, registry = synthetic()
        correction["corrections"] = {}
        correction["accepted_exclusions"] = {"pc_demo": [{"name": "B", "source_key": "Op|Main|2", "reason": "not served"}]}
        validate(corridors, chains, pool, correction, registry)
        correction["accepted_exclusions"]["pc_demo"][0]["reason"] = ""
        with self.assertRaises(AssertionError):
            validate(corridors, chains, pool, correction, registry)

    def test_new_ids_must_reuse_the_browse_registry(self):
        corridors, chains, pool, correction, registry = synthetic()
        correction["corrections"]["pc_demo"]["reuse_ids"]["B"]["station_id"] = "sta_new"
        with self.assertRaisesRegex(AssertionError, "reuse"):
            validate(corridors, chains, pool, correction, registry)

    def test_applied_status_requires_official_order(self):
        corridors, chains, pool, correction, registry = synthetic()
        correction["status"] = "APPLIED"
        with self.assertRaises(AssertionError):
            validate(corridors, chains, pool, correction, registry)
        chains["pc_demo"].insert(1, {"name": "B", "point": (139.7005, 35.71)})
        validate(corridors, chains, pool, correction, registry)
        chains["pc_demo"][1], chains["pc_demo"][2] = chains["pc_demo"][2], chains["pc_demo"][1]
        with self.assertRaises(AssertionError):
            validate(corridors, chains, pool, correction, registry)


class CommittedCorridorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = load_yaml(ROOT / "data/reference/PHASE1_IDENTITY_RULES.yml")["corridors"]
        stations = pq.read_table(ROOT / "data/derived/stations.parquet").to_pylist()
        crosswalk = pq.read_table(ROOT / "data/derived/station_line_crosswalk.parquet").to_pylist()
        network = json.loads((ROOT / "dist/network.json").read_text(encoding="utf-8"))
        cls.registry = json.loads((ROOT / "data/reference/NETWORK_IDENTITY_REGISTRY.json").read_text(encoding="utf-8"))["maps"]
        cls.chains = corridor_chains(stations, crosswalk)
        cls.pool = build_pool(stations, network["stations"])
        cls.correction = load_yaml(ROOT / "data/reference/G2_CORRIDOR_CORRECTION_2026-09-28.yml")

    def test_committed_segments_pass_with_recorded_correction(self):
        validate(self.rules, self.chains, self.pool, self.correction, self.registry)

    def test_known_keihin_tohoku_and_sobu_omissions_are_detected_without_the_record(self):
        correction = copy.deepcopy(self.correction)
        correction["corrections"] = {}
        with self.assertRaises(AssertionError) as raised:
            validate(self.rules, self.chains, self.pool, correction, self.registry)
        message = str(raised.exception)
        self.assertIn("pc_jr_sobu_local", message)
        gaps = find_gaps(self.rules, self.chains, self.pool, 1.3)
        missing = {g["name"] for g in gaps["pc_jr_keihin_tohoku_negishi"]} | {g["name"] for g in gaps["pc_jr_sobu_local"]}
        self.assertTrue({"与野", "北浦和", "西日暮里", "日暮里", "鶯谷", "小岩"} <= missing)


if __name__ == "__main__":
    unittest.main()
