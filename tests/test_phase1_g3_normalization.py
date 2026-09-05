import unittest

from scripts.normalize_phase1_g3 import (
    ECONOMIC_METRIC_COLUMNS,
    annotate_prefecture_partition_overlap,
    geo_metadata,
    mesh_500m_bounds,
    point_wkb,
    polygon_wkb,
)


class G3NormalizationUtilityTest(unittest.TestCase):
    def test_middle_industry_columns_are_fixed_to_official_definition(self):
        self.assertEqual(ECONOMIC_METRIC_COLUMNS["retail_establishments"], "T001163062")
        self.assertEqual(ECONOMIC_METRIC_COLUMNS["food_establishments"], "T001163080")
        self.assertEqual(ECONOMIC_METRIC_COLUMNS["lifestyle_leisure_establishments"], "T001163084")
        self.assertEqual(ECONOMIC_METRIC_COLUMNS["retail_employees"], "T001163291")
        self.assertEqual(ECONOMIC_METRIC_COLUMNS["food_employees"], "T001163345")
        self.assertEqual(ECONOMIC_METRIC_COLUMNS["lifestyle_leisure_employees"], "T001163357")

    def test_fourth_level_mesh_geometry(self):
        min_lon, min_lat, max_lon, max_lat = mesh_500m_bounds("533945511")
        self.assertAlmostEqual(min_lon, 139.6375)
        self.assertAlmostEqual(min_lat, 35.708333333333336)
        self.assertAlmostEqual(max_lon - min_lon, 1 / 160)
        self.assertAlmostEqual(max_lat - min_lat, 1 / 240)
        self.assertEqual(polygon_wkb((min_lon, min_lat, max_lon, max_lat))[0], 1)

    def test_invalid_mesh_code_fails(self):
        with self.assertRaises(ValueError):
            mesh_500m_bounds("533945510")
        with self.assertRaises(ValueError):
            mesh_500m_bounds("not-a-mesh")

    def test_point_wkb_uses_little_endian_point_type(self):
        self.assertEqual(point_wkb(139.7, 35.6)[:5], b"\x01\x01\x00\x00\x00")

    def test_cross_prefecture_mesh_components_are_preserved_not_dropped(self):
        rows = [
            {"mesh_code": "533945511", "prefecture_partition_code": "12", "source_record_key": "533945511"},
            {"mesh_code": "533945511", "prefecture_partition_code": "13", "source_record_key": "533945511"},
        ]
        summary = annotate_prefecture_partition_overlap(rows, "economic-2021")
        self.assertEqual(summary["distinct_mesh_count"], 1)
        self.assertEqual(summary["cross_partition_mesh_count"], 1)
        self.assertEqual(rows[0]["mesh_partition_observation_id"], "economic-2021:12:533945511")
        self.assertEqual(
            rows[1]["cross_partition_rollup_status"],
            "requires_scope_aware_prefecture_component_sum",
        )

    def test_geoparquet_crs_is_inline_projjson(self):
        import json

        metadata = geo_metadata(["Polygon"])
        crs = json.loads(metadata[b"geo"])["columns"]["geometry"]["crs"]
        self.assertEqual(crs["type"], "GeographicCRS")
        self.assertEqual(crs["id"], {"authority": "EPSG", "code": 6668})


if __name__ == "__main__":
    unittest.main()
