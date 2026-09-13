"""Clone-safe checks of the new public station inventory and source lineage."""
import hashlib
import json
from pathlib import Path
import unittest
import yaml
ROOT=Path(__file__).resolve().parents[1]
N=json.loads((ROOT/'dist/network.json').read_text())
B=json.loads((ROOT/'dist/data.json').read_text())
A=json.loads((ROOT/'data/manifests/network_identity.json').read_text())

class NetworkTests(unittest.TestCase):
    def test_scope_identity_and_provenance(self):
        from scripts.build_public_network import inside
        scope=json.loads((ROOT/'data/reference/NETWORK_SCOPE.json').read_text())
        self.assertEqual(N['scope'],scope)
        self.assertFalse(scope['isMunicipalityBoundary']);self.assertFalse(scope['isCommercialCenterBoundary'])
        self.assertEqual(N['baseDataSha256'],hashlib.sha256((ROOT/'dist/data.json').read_bytes()).hexdigest())
        old=yaml.safe_load((ROOT/'data/reference/PHASE1_IDENTITY_REGISTRY.yml').read_text())['maps']
        new=json.loads((ROOT/'data/reference/NETWORK_IDENTITY_REGISTRY.json').read_text())['maps']
        station_alias={**new['station'],**old['station']}
        self.assertEqual(len(A['records']),1592);self.assertEqual(A['unresolved'],[])
        for r in A['records']: self.assertEqual(station_alias[r['sourceKey']],r['stationId'])
        for s in N['stations']:
            self.assertTrue(inside(*s['coordinates'],scope['polygon']),s['name'])
            self.assertRegex(s['id'],r'^sta_[0-9a-f]{32}$')
            self.assertRegex(s['groupId'],r'^stg_[0-9a-f]{32}$')
            self.assertEqual(s['routeIds'],[]);self.assertEqual(s['routePositions'],{})
        hashes={a['artifact_id']:a['sha256'] for a in yaml.safe_load((ROOT/'data/manifests/source_lock.phase1.yml').read_text())['artifacts']}
        self.assertTrue({'n02-25-gml','s12-25-gml'}<={a['id'] for a in N['sourceArtifacts']})
        for a in N['sourceArtifacts']:self.assertEqual(a['sha256'],hashes[a['id']])

    def test_raw_tokens_statuses_and_spatial_partitions_remain_separate(self):
        for s in N['stations']:
            r=s['ridership'];self.assertEqual(r['fiscalYear'],2024);self.assertFalse(r['summationAllowed'])
            eligible=[o for o in r['observations'] if o['status'] in ('observed','observed_zero')]
            if r['value'] is not None:self.assertEqual(len(eligible),1);self.assertEqual(r['value'],eligible[0]['value'])
            else:self.assertNotEqual(r['status'],'observed')
        for m,c in N['meshContexts'].items():
            self.assertNotIn(m,B['meshContexts']);self.assertFalse(c['fullMeshRollup'])
            for family in ['economicComponents','populationComponents']:
                self.assertEqual(len(c[family]),len({x['prefectureCode'] for x in c[family]}))
                for row in c[family]:
                    self.assertIn(row['prefectureCode'],['11','12','13','14'])
                    self.assertIn(row['prefectureCode'],row['sourcePartitionCodes'])
            for row in c['economicComponents']:
                for k in ['restaurants','retail','apparel','employees']:
                    self.assertIn('raw',row[k])
                    if row[k]['status'] not in ['observed','observed_zero']:self.assertIsNone(row[k]['value'])
        for c in N['studentMeshContexts'].values():
            self.assertFalse(c['fullMeshRollup'])
            for row in c['components']:
                self.assertEqual(row['referenceDate'],'2020-10-01')
                self.assertEqual(row['university']['column'],'T001144046')
                self.assertIn('rawProcessing',row)

if __name__=='__main__':unittest.main()
