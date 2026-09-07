"""The public reference catalog must not pretend to be a statistical center dataset."""
import hashlib
import json
from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]


class PublicExplorerTests(unittest.TestCase):
    def test_public_candidates_are_allowlisted_reference_fields(self):
        data = json.loads((ROOT / 'dist/data.json').read_text())
        registry = yaml.safe_load((ROOT / 'data/reference/GOLDEN_EVALS.yml').read_text())
        expected = {c['golden_eval_id']: c for c in registry['cases']
                    if c['split'] == 'calibration' and '茨城県' not in c['prefectures']}
        self.assertEqual(len(data['cases']), 44)
        self.assertEqual({c['id'] for c in data['cases']}, set(expected))
        for c in data['cases']:
            self.assertEqual(set(c), {'id','name','prefectures','stations','corridors','features','x','y','scale','scaleStatus'})
            self.assertEqual(c['name'], expected[c['id']]['display_name_ja'])
            self.assertEqual(c['stations'], expected[c['id']]['anchor_station_names'])
            self.assertIsNone(c['scale'])
            self.assertEqual(c['scaleStatus'], 'not_estimated')
        for name, sha in data['sourceHashes'].items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), sha)

    def test_eight_reference_routes_preserve_order_and_unique_counts(self):
        data = json.loads((ROOT / 'dist/data.json').read_text())
        pilots = yaml.safe_load((ROOT / 'data/reference/PILOT_LINES.yml').read_text())['pilot_corridors']
        by_name = {c['name']: c['id'] for c in data['cases']}
        self.assertEqual(len(data['routes']), 8)
        for route, pilot in zip(data['routes'], pilots):
            self.assertEqual(route['id'], pilot['pilot_corridor_id'])
            self.assertEqual(route['caseIds'], [by_name[n] for n in pilot['anchor_cases'] if n in by_name])
            self.assertEqual(len(set(route['caseIds'])), len(route['caseIds']))
        self.assertEqual(data['routes'][-1]['end'], '柏たなか')

    def test_static_bundle_has_no_unreviewed_payloads_or_external_runtime_dependencies(self):
        files = {p.name for p in (ROOT / 'dist').iterdir()}
        self.assertEqual(files, {'index.html','style.css','app.mjs','data.json'})
        html = (ROOT / 'dist/index.html').read_text()
        for name in ['style.css', 'app.mjs']:
            self.assertIn('./' + name, html)
        self.assertNotIn('<script src="http', html)
        self.assertIn('距離・境界・街の大きさを表しません', html)


if __name__ == '__main__':
    unittest.main()
