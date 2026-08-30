from decimal import Decimal
import unittest

from scripts.observation_semantics import (
    normalize_census_count,
    normalize_estat_count,
    normalize_s12_count,
)


class EStatSemanticsTest(unittest.TestCase):
    def test_true_zero_is_explicit(self):
        result = normalize_estat_count("0")
        self.assertEqual(result.status, "observed_zero")
        self.assertEqual(result.numeric_value, Decimal("0"))

    def test_missing_tokens_are_not_zero(self):
        cases = {
            "": "source_absent",
            "X": "suppressed",
            "...": "not_surveyed",
            "-": "not_applicable",
        }
        for token, expected in cases.items():
            with self.subTest(token=token):
                result = normalize_estat_count(token)
                self.assertEqual(result.status, expected)
                self.assertIsNone(result.numeric_value)

    def test_unknown_token_fails(self):
        with self.assertRaises(ValueError):
            normalize_estat_count("unknown")

    def test_negative_count_fails(self):
        with self.assertRaises(ValueError):
            normalize_estat_count("-1")


class S12SemanticsTest(unittest.TestCase):
    def test_nonpublic_is_not_zero(self):
        result = normalize_s12_count("", existence_code="3", duplicate_code="1")
        self.assertEqual(result.status, "not_public")
        self.assertIsNone(result.numeric_value)

    def test_duplicate_record_is_not_added(self):
        result = normalize_s12_count("123", existence_code="1", duplicate_code="2")
        self.assertEqual(result.status, "duplicate_on_other_record")
        self.assertIsNone(result.numeric_value)

    def test_station_absent_takes_precedence(self):
        result = normalize_s12_count("0", existence_code="4", duplicate_code="1")
        self.assertEqual(result.status, "station_absent")
        self.assertIsNone(result.numeric_value)


class CensusSemanticsTest(unittest.TestCase):
    def test_suppressed_source_is_not_zero(self):
        result = normalize_census_count("", suppression_processing_code="2")
        self.assertEqual(result.status, "suppressed")
        self.assertIsNone(result.numeric_value)

    def test_aggregation_destination_remains_distinct(self):
        result = normalize_census_count("42", suppression_processing_code="1")
        self.assertEqual(result.status, "aggregation_destination")
        self.assertEqual(result.numeric_value, Decimal("42"))


if __name__ == "__main__":
    unittest.main()
