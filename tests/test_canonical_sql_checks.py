import sqlite3
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# DATA_DICTIONARY.md §2: (status, numeric_value) -> accepted?
# Two points where the dictionary and the SQL disagree stay out of this test until the
# Owner decides them (docs/PROPOSED_DECISIONS_2026-09-28.md): whether `imputed` may be
# NULL, and whether an `invalid` row may be stored at all. Only the case both options
# agree on is pinned: an `invalid` row never carries a number.
CASES = [
    ("observed", 12.0, True),
    ("observed", 0.0, False),
    ("observed", None, False),
    ("observed_zero", 0.0, True),
    ("observed_zero", 1.0, False),
    ("observed_zero", None, False),
    ("aggregation_destination", 7.0, True),
    ("aggregation_destination", None, False),
    ("unknown_status", None, False),
    ("invalid", 0.0, False),
] + [
    (status, value, value is None)
    for status in [
        "suppressed", "not_public", "not_surveyed", "not_applicable", "source_absent",
        "duplicate_on_other_record", "station_absent", "outside_scope",
    ]
    for value in [None, 0.0]
]


class CanonicalObservationCheckTest(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.executescript((ROOT / "schema/canonical.sql").read_text(encoding="utf-8"))
        # Only the row-level CHECK is under test; referenced lookup rows are out of scope.
        self.connection.execute("PRAGMA foreign_keys = OFF")

    def tearDown(self):
        self.connection.close()

    def insert(self, index, status, value):
        self.connection.execute(
            """
            INSERT INTO feature_observation (
                observation_id, entity_type, entity_id, metric_code, numeric_value, raw_value,
                observation_status, unit, source_release_id, source_record_key, retrieved_at,
                provenance_json
            ) VALUES (?, 'mesh', 'mesh_1', 'metric', ?, 'raw', ?, 'count', 'release', ?, '2026-09-28', '{}')
            """,
            (f"obs_{index}", value, status, f"record_{index}"),
        )

    def test_every_status_value_pair_matches_the_dictionary(self):
        for index, (status, value, accepted) in enumerate(CASES):
            with self.subTest(status=status, value=value):
                if accepted:
                    self.insert(index, status, value)
                else:
                    with self.assertRaises(sqlite3.IntegrityError):
                        self.insert(index, status, value)


if __name__ == "__main__":
    unittest.main()
