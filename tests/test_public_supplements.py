"""Clone-safe validation of source provenance and extra public data (no browser)."""
import json
from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / 'dist' / name).read_text())


class PublicSupplementTests(unittest.TestCase):
    def test_students_match_pilot_and_preserve_processing(self):
        data, students = load('data.json'), load('students.json')
        self.assertEqual(set(students['meshContexts']), set(data['meshContexts']))
        self.assertEqual(students['coverage']['componentCount'], 221)
        self.assertFalse(students['interpretation']['commutingInflowAvailable'])
        for source in students['sources']:
            self.assertEqual(source['referenceDate'], '2020-10-01')
            self.assertIsNone(source['publicationDate'])
            self.assertEqual(source['publicationDateStatus'], 'table_specific_date_not_confirmed')
        for ctx in students['meshContexts'].values():
            self.assertFalse(ctx['fullMeshRollup'])
            for c in ctx['components']:
                self.assertEqual(c['processingCode'], c['rawProcessing']['HTKSYORI'])
                self.assertIn(c['prefectureCode'], c['sourcePartitionCodes'])
                for key in students['metrics']:
                    obs = c[key]
                    self.assertIn('raw', obs)
                    if obs['status'] not in ['observed', 'observed_zero', 'aggregation_destination']:
                        self.assertIsNone(obs['value'])

    def test_district_source_scope_values_and_zero_precision(self):
        asset = load('commercial-districts.json')
        self.assertEqual(asset['counts'], {'11': 574, '12': 530, '13': 1044, '14': 558})
        self.assertEqual(asset['source']['sales_reference_period'], '2020-01-01/2020-12-31')
        self.assertEqual(asset['source']['published_date'], '2024-06-25')
        self.assertEqual(len({d['source_district_id'] for d in asset['districts']}), 2706)
        for district in asset['districts']:
            self.assertNotIn('center_id', district)
            self.assertNotIn('station_id', district)
            self.assertTrue(district['municipality_name'])
            obs = [district['metrics'][k] for k in ['retail_sales_million_yen', 'food_service_sales_million_yen', 'personal_service_sales_million_yen']]
            if any(o['value'] is None for o in obs):
                self.assertIsNone(district['three_sector_sales_million_yen'])
            else:
                self.assertEqual(district['three_sector_sales_million_yen'], sum(o['value'] for o in obs))
            for o in obs:
                if o['value'] == 0:
                    self.assertEqual(o['status'], 'below_rounding_unit')

    def test_cafe_selection_symbols_and_source_dates(self):
        asset = load('cafes.json')
        self.assertEqual(asset['qa']['statuses'], {'observed': 252, 'symbol_unresolved': 6})
        self.assertEqual(asset['source']['reference_date'], '2021-06-01')
        self.assertEqual(asset['source']['official_publication_date'], '2023-06-27')
        for row in asset['observations']:
            self.assertEqual((row['industry_code'], row['organization_code'], row['employee_size_code']), ('767', '1', '00'))
            if row['status'] == 'symbol_unresolved':
                self.assertIsNone(row['value'])
                self.assertFalse(row['approved_for_display'])
        self.assertEqual(len({r['area_code'] for r in asset['observations']}), 258)
        self.assertTrue(all(c['pass'] for c in asset['qa']['sum_checks']))

    def test_manifest_freezes_six_raw_sources_with_accepted_terms(self):
        lock = yaml.safe_load((ROOT / 'data/manifests/public_supplements.yml').read_text())
        self.assertFalse(lock['n03_used'])
        self.assertEqual(len(lock['artifacts']), 6)
        for artifact in lock['artifacts']:
            self.assertEqual(artifact['reuse_status'], 'accepted_official_eStat_terms_with_attribution')
            self.assertRegex(artifact['sha256'], r'^[0-9a-f]{64}$')
            meta = json.loads((ROOT / artifact['source_metadata']).read_text())
            self.assertEqual(artifact['sha256'], meta.get('sha256', meta.get('response_sha256')))


if __name__ == '__main__':
    unittest.main()
