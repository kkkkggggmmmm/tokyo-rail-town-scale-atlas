"""Public quantitative payload: scope, immutable provenance, status and safe assets."""
import hashlib
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
import yaml
ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/'dist/data.json').read_text())
C=json.loads((ROOT/'dist/context.json').read_text())
class PublicExplorerTests(unittest.TestCase):
    def test_public_scope_and_existing_identity(self):
        self.assertEqual(len(D['routes']),8)
        self.assertEqual(len(D['stations']),226)
        self.assertEqual(len({s['id'] for s in D['stations']}),226)
        names={s['name'] for s in D['stations']}
        self.assertTrue({'東京','新宿','横浜','吉祥寺','柏たなか'} <= names)
        self.assertFalse(names & {'守谷','みらい平','みどりの','万博記念公園','研究学園','つくば'})
        all_ids={s['id'] for s in D['stations']}
        for route in D['routes']:
            self.assertEqual(len(route['stationIds']),len(set(route['stationIds'])))
            self.assertTrue(set(route['stationIds']) <= all_ids)
        for s in D['stations']:
            self.assertRegex(s['id'],r'^sta_[a-f0-9]{32}$')
            self.assertRegex(s['groupId'],r'^stg_[a-f0-9]{32}$')
            lon,lat=s['coordinates'];west,south,east,north=D['meshContexts'][s['meshCode']]['bounds']
            self.assertTrue(west<=lon<east and south<=lat<north)
            self.assertEqual(s['officialRouteCount'],len({(r['operator'],r['route']) for r in s['officialRouteMemberships']}))
        self.assertFalse(D['scope']['centerEstimates'])
        self.assertFalse(D['scope']['wholeMeshRollups'])
        self.assertNotIn('cases',D)

    def test_source_lock_and_observation_semantics(self):
        lock=yaml.safe_load((ROOT/'data/manifests/source_lock.phase1.yml').read_text())
        hashes={a['artifact_id']:a['sha256'] for a in lock['artifacts']}
        for artifact in D['sourceArtifacts']:
            self.assertEqual(artifact['sha256'],hashes[artifact['id']])
        econ=next(s for s in D['sources'] if s['id']=='economic')
        self.assertEqual(econ['metrics']['restaurants'],'T001163082')
        self.assertEqual(econ['metrics']['apparel'],'T001163064')
        self.assertEqual(econ['referenceDate'],'2021-06-01')
        dup=0
        for s in D['stations']:
            r=s['ridership'];self.assertEqual(r['fiscalYear'],2024);self.assertFalse(r['summationAllowed'])
            self.assertEqual(len(r['observations']),len({o['sourceRecordKey'] for o in r['observations']}))
            if r['status']=='duplicate_on_other_record':
                dup+=1;self.assertIsNone(r['value'])
            if r['value'] is not None:
                eligible=[o for o in r['observations'] if o['status'] in ['observed','observed_zero']]
                self.assertEqual(len(eligible),1);self.assertEqual(r['value'],eligible[0]['value'])
        self.assertEqual(dup,16)
        for mesh in D['meshContexts'].values():
            self.assertFalse(mesh['fullMeshRollup'])
            for c in mesh['economicComponents']:
                self.assertIn(c['prefectureCode'],{'11','12','13','14'})
                for k in ['restaurants','retail','employees','apparel']:
                    o=c[k]
                    if o['status'] not in ['observed','observed_zero']:self.assertIsNone(o['value'])
                    self.assertIn('raw',o)
            for c in mesh['populationComponents']:
                self.assertEqual(c['referenceDate'],'2020-10-01')
                self.assertIn('processingCode',c);self.assertIn('aggregatedSourceMeshCodes',c)

    def test_context_preserves_scope_license_and_missing_education(self):
        self.assertEqual(len(C['economy']['records']),7)
        for row in C['economy']['records']:
            self.assertTrue(row['approved_for_public_display'])
            self.assertIn(row['scope_type'],{'municipality','town'})
            for field in ['sourceUrl','geographyLabel','periodLabel','unit','attribution','termsUrl']:self.assertTrue(row[field])
        gdp=next(x for x in C['economy']['records'] if x.get('metric_id')=='municipal_gdp_nominal')
        self.assertEqual((gdp['value'],gdp['unit'],gdp['scope_label']),(152130,'億円','横浜市全域'))
        edu=C['educationSafety'];self.assertIsNone(edu['middleSchoolExamRate']['value'])
        self.assertEqual({r['municipality']:r['value'] for r in edu['crime']['records']},{'横浜市':18925,'川崎市':8256})
        for r in edu['crime']['records']:
            self.assertEqual(r['periodEnd'],'2025-12-31');self.assertIsNone(r['per10000Residents'])
        self.assertEqual(len(edu['cramSchools']['records']),7)
        self.assertTrue(all(x['presence'] for x in edu['cramSchools']['records']))

    def test_static_assets_are_allowlisted_and_chart_is_real_svg(self):
        expected={'index.html','style.css','app.mjs','network.json','network-model.mjs','data.json','context.json','route-comparison.svg',
                  'students.json','cafes.json','commercial-districts.json','supplements.mjs','supplement-views.mjs','explorer-model.mjs','atlas-insights.mjs','theme-view.mjs','district-areas.mjs',
                  'vendor/maplibre-gl.js','vendor/maplibre-gl.css','vendor/pmtiles.js','vendor/MAPLIBRE-LICENSE.txt','vendor/PMTILES-LICENSE.txt'}
        files={str(p.relative_to(ROOT/'dist')) for p in (ROOT/'dist').rglob('*') if p.is_file()}
        self.assertEqual(files,expected)
        html=(ROOT/'dist/index.html').read_text();self.assertNotIn('<script src="http',html)
        for f in ['maplibre-gl.js','maplibre-gl.css','pmtiles.js']:self.assertIn('./vendor/'+f,html)
        self.assertNotIn('買い物2',html)
        svg=ET.parse(ROOT/'dist/route-comparison.svg').getroot()
        self.assertEqual(svg.tag,'{http://www.w3.org/2000/svg}svg')
        all_text=''.join(svg.itertext())
        for name in [r['name'] for r in D['routes']]:self.assertIn(name,all_text)
        self.assertIn('2021年',all_text)
        self.assertIn('CoreScale',all_text)
if __name__=='__main__':unittest.main()
