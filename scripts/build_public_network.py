#!/usr/bin/env python3
"""Extend the published pilot with every unambiguous N02 station in a fixed scope.

Consumes only hash-locked originals. No network, service-order inference,
administrative allocation, ridership sums or commercial-center estimates.
Use --mint-ids once to extend the persistent opaque identity registry.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import uuid
from zipfile import ZipFile
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_phase1_identity import load_n02
from scripts.build_public_quantitative import mesh_code, METRICS, PUBLIC_PREFECTURES
from scripts.normalize_phase1_g3 import estat_rows, mesh_500m_bounds, int_or_none, clean_text
from scripts.observation_semantics import normalize_estat_count, normalize_census_count, normalize_s12_count


def inside(lon, lat, polygon):
    """Ray casting, including boundary points, for our explicit simple polygon."""
    hit = False
    for (a, b), (c, d) in zip(polygon, polygon[1:]):
        cross = (lon-a)*(d-b)-(lat-b)*(c-a)
        if abs(cross) < 1e-12 and min(a,c) <= lon <= max(a,c) and min(b,d) <= lat <= max(b,d):
            return True
        if (b > lat) != (d > lat) and lon < (c-a)*(lat-b)/(d-b)+a:
            hit = not hit
    return hit


def access_records(artifact):
    by_key, ordinals = defaultdict(list), Counter()
    with ZipFile(ROOT/artifact['local_path']) as archive:
        features = json.loads(archive.read('S12-25_GML/UTF-8/S12-25_NumberOfPassengers.geojson'))['features']
    for f in features:
        p = f['properties']; key = '|'.join(str(p.get(k,'')) for k in ('S12_002','S12_003','S12_001c'))
        ordinals[key] += 1
        duplicate, existence = clean_text(p.get('S12_058')), clean_text(p.get('S12_059'))
        o = normalize_s12_count(p.get('S12_061'), existence_code=existence, duplicate_code=duplicate)
        by_key[key].append({'value':int_or_none(o.numeric_value),'raw':o.raw_value,'status':o.status,
            'sourceKey':key,'sourceRecordKey':f'{key}|feature={ordinals[key]}',
            'duplicateCode':duplicate,'existenceCode':existence,'note':clean_text(p.get('S12_060'))})
    return by_key


def select_access(obs):
    eligible = [o for o in obs if o['status'] in ('observed','observed_zero')]
    chosen = eligible[0] if len(eligible)==1 else None
    status = chosen['status'] if chosen else ('ambiguous_multiple_records' if len(eligible)>1 else
        obs[0]['status'] if obs and len({o['status'] for o in obs})==1 else 'source_absent')
    return {'fiscalYear':2024,'value':chosen['value'] if chosen else None,'status':status,
        'measureLabel':'S12掲載の1日当たり駅別乗降客数','unit':'人/日','sourceId':'s12',
        'selection':'single_observed_source_feature' if chosen else 'no_unambiguous_observed_feature',
        'note':chosen['note'] if chosen else None,'observations':obs,
        'hasDuplicateRecords':any(o['duplicateCode']=='2' for o in obs),'summationAllowed':False}


def contexts_for(wanted, artifacts):
    contexts = {m:{'bounds':list(mesh_500m_bounds(m)),'economicComponents':[], 'populationComponents':[],
        'label':'駅の座標を含む500m区画・都県公表分','fullMeshRollup':False} for m in sorted(wanted)}
    families = {'estat_economic_census_mesh_2021':'economicComponents','estat_population_census_mesh_2020':'populationComponents'}
    for a in artifacts:
        family = families.get(a['source_id'])
        if not family: continue
        pref = str(a['prefecture_code']).zfill(2)
        for row_number, raw in estat_rows(a):
            m=raw['KEY_CODE'].strip()
            if m not in wanted: continue
            c={'prefectureCode':pref,'sourceArtifactId':a['artifact_id'],'sourceRowNumber':row_number,
                'observationId':f'{"economic-2021" if family=="economicComponents" else "population-2020"}:{pref}:{m}'}
            if family=='economicComponents':
                c['referenceDate']='2021-06-01'
                for metric, column in METRICS.items():
                    o=normalize_estat_count(raw[column])
                    c[metric]={'value':int_or_none(o.numeric_value),'raw':o.raw_value,'status':o.status}
            else:
                code=clean_text(raw['HTKSYORI']); o=normalize_census_count(raw['T001141001'],suppression_processing_code=code)
                c.update(referenceDate='2020-10-01',value=int_or_none(o.numeric_value),raw=o.raw_value,status=o.status,
                    processingCode=code,aggregationTarget=clean_text(raw['HTKSAKI']),aggregatedSourceMeshCodes=clean_text(raw['GASSAN']))
            contexts[m][family].append(c)
    for m,c in contexts.items():
        outside=set()
        for family in families.values():
            cs=sorted(c[family],key=lambda x:x['prefectureCode']); codes=[x['prefectureCode'] for x in cs]
            assert len(codes)==len(set(codes)), f'duplicate partition in {m}'
            outside.update(set(codes)-PUBLIC_PREFECTURES)
            for row in cs:
                row['sourcePartitionCodes']=codes
                row['rollupStatus']='requires_scope_aware_prefecture_component_sum' if len(codes)>1 else 'single_prefecture_component'
            c[family]=[row for row in cs if row['prefectureCode'] in PUBLIC_PREFECTURES]
        c.update(economicStatus='available' if c['economicComponents'] else 'source_absent',
            populationStatus='available' if c['populationComponents'] else 'source_absent',outsidePublicComponentCodes=sorted(outside))
    return contexts


def student_contexts_for(contexts):
    """Same accepted T001144 source/definitions, now for additional station meshes."""
    manifest=yaml.safe_load((ROOT/'data/manifests/public_supplements.yml').read_text())
    fields={'university':'T001144046','juniorCollege':'T001144043','highSchool':'T001144040','allStudents':'T001144034'}
    result={m:{'components':[],'fullMeshRollup':False} for m in contexts}
    selected=[a for a in manifest['artifacts'] if '/student/' in a['path']]
    assert len(selected)==4
    for a in selected:
        path=ROOT/a['path']; assert a['reuse_status']=='accepted_official_eStat_terms_with_attribution'
        assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==a['sha256'], f'locked student raw missing/drift: {path}'
        pref=path.stem[-2:]; sid=f'estat-census-2020-student-500m-jgd2011-{pref}'
        for number,row in estat_rows({'local_path':a['path']}):
            m=row['KEY_CODE'].strip()
            if m not in result: continue
            c={'prefectureCode':pref,'sourceId':sid,'sourceRowNumber':number,'referenceDate':'2020-10-01',
                'processingCode':row['HTKSYORI'],'aggregationTarget':row['HTKSAKI'] or None,
                'aggregatedSourceMeshCodes':row['GASSAN'] or None,
                'rawProcessing':{k:row[k] for k in ['KEY_CODE','HTKSYORI','HTKSAKI','GASSAN']}}
            for k,col in fields.items():
                o=normalize_census_count(row[col],suppression_processing_code=row['HTKSYORI'])
                c[k]={'value':int_or_none(o.numeric_value),'raw':o.raw_value,'status':o.status,'column':col}
            result[m]['components'].append(c)
    for m,ctx in result.items():
        codes=sorted({c['prefectureCode'] for c in ctx['components']}|{p for c in contexts[m]['populationComponents'] for p in c['sourcePartitionCodes']})
        for c in ctx['components']: c['sourcePartitionCodes']=codes
        ctx['sourcePartitionCodes']=codes
        ctx['status']='available' if ctx['components'] else 'source_absent'
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--mint-ids',action='store_true'); args=parser.parse_args()
    scope=json.loads((ROOT/'data/reference/NETWORK_SCOPE.json').read_text())
    base=json.loads((ROOT/'dist/data.json').read_text())
    lock=yaml.safe_load((ROOT/'data/manifests/source_lock.phase1.yml').read_text()); artifacts=lock['artifacts']
    # Restore/check the full bundle, never silently update its hash on acquisition drift.
    for a in artifacts:
        path=ROOT/a['local_path']
        assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==a['sha256'], f'locked raw missing/drift: {a["artifact_id"]}'
    original=yaml.safe_load((ROOT/'data/reference/PHASE1_IDENTITY_REGISTRY.yml').read_text())['maps']
    registry_path=ROOT/'data/reference/NETWORK_IDENTITY_REGISTRY.json'
    registry=json.loads(registry_path.read_text()) if registry_path.exists() else {
        'version':'1.0.0','sourceRelease':'N02-25','scopeVersion':scope['version'],'mintedAt':'2026-09-13',
        'maps':{'station':{},'station_group':{},'official_route':{}}}
    def identity(kind,key):
        if key in original.get(kind,{}): return original[kind][key]
        target=registry['maps'][kind]
        if key not in target:
            assert args.mint_ids, f'Identity absent; review then explicitly mint {kind}: {key}'
            target[key]={'station':'sta','station_group':'stg','official_route':'nrt'}[kind]+'_'+uuid.uuid4().hex
        return target[key]
    all_rows=[s for rs in load_n02().values() for s in rs]
    old={s['id']:s for s in base['stations']}; groups=defaultdict(set)
    for s in all_rows: groups[s['group_code']].add((s['operator'],s['route']))
    candidates=[s for s in all_rows if inside(s['lon'],s['lat'],scope['polygon'])]
    # Include historical public records outside the new window without claiming that
    # their whole corridors are newly covered.
    candidate_keys={s['source_key'] for s in candidates}
    included=candidates+[s for s in all_rows if s['source_key'] not in candidate_keys and original['station'].get(s['source_key']) in old]
    unresolved=[]; safe=[]
    for s in included:
        reasons=[]
        if len(s['name_variants'])!=1 or len(s['group_variants'])!=1: reasons.append('ambiguous_source_identity')
        if not all(s[k] for k in ('operator','route','name','group_code')) or s['station_code'].startswith('MISSING'): reasons.append('missing_identity_attribute')
        if reasons: unresolved.append({'sourceKey':s['source_key'],'reasons':reasons,'featureIndexes':s['feature_indexes']})
        else: safe.append(s)
    # Ambiguity blocks publication; retain a review artifact, do not improvise a merge.
    if unresolved:
        (ROOT/'data/manifests/network_unresolved.json').write_text(json.dumps(unresolved,ensure_ascii=False,indent=2)+'\n')
        raise RuntimeError('Unresolved station identity; publication stopped')
    access=access_records(next(a for a in artifacts if a['artifact_id']=='s12-25-gml'))
    stations=[]; memberships={}; routes={}; audit=[]
    for s in safe:
        sid=identity('station',s['source_key']); group=identity('station_group',s['group_code'])
        rk=s['operator']+'|'+s['route']; rid=identity('official_route',rk)
        route=routes.setdefault(rid,{'id':rid,'name':s['route'],'operator':s['operator'],'sourceKey':rk,'stationIds':[],
            'orderStatus':'unconfirmed','scope':'掲載範囲内のN02正式路線。運行系統や路線全長ではない。'})
        route['stationIds'].append(sid); memberships[sid]=[rid]
        if sid not in old:
            official=sorted(groups[s['group_code']]); lon,lat=round(s['lon'],7),round(s['lat'],7)
            stations.append({'id':sid,'groupId':group,'name':s['name'],'operator':s['operator'],
                'coordinates':[lon,lat],'coordinateCRS':'EPSG:6668','routeIds':[],'routePositions':{},
                'sourceStationKey':s['source_key'],'sourceStationGroupKey':s['group_code'],
                'officialRouteCount':len(official),'officialRouteMemberships':[{'operator':op,'route':r} for op,r in official],
                'officialRouteCountLabel':'N02の同一駅群に属する正式路線数（運行系統数ではない）',
                'ridership':select_access(access.get(s['source_key'],[])),'meshCode':mesh_code(lon,lat)})
        else:
            assert old[sid]['groupId']==group, f'old group ID conflict: {sid}'
            assert old[sid]['officialRouteCount']==len(groups[s['group_code']]), f'old route count drift: {sid}'
        audit.append({'sourceKey':s['source_key'],'stationId':sid,'groupId':group,'sourceFeatureIndexes':s['feature_indexes'],
            'selection':'scope_polygon' if s['source_key'] in candidate_keys else 'retained_pilot','identityStatus':'normalized'})
    assert len({s['id'] for s in stations})==len(stations)
    assert set(old)<=set(memberships), 'Existing station omitted'
    wanted={s['meshCode'] for s in stations}-set(base['meshContexts'])
    contexts=contexts_for(wanted,artifacts)
    students=student_contexts_for(contexts)
    merged=base['stations']+stations; merged_contexts={**contexts,**base['meshContexts']}
    coverage={'stationCount':len(merged),'stationGroupCount':len({s['groupId'] for s in merged}),
        'addedStationRecords':len(stations),'scopeStationRecords':len(candidates),
        'retainedOutsideScopeRecords':len(included)-len(candidates),'officialRouteCount':len(routes),
        'meshCount':len(merged_contexts),'unresolvedStationRecords':len(unresolved),
        'accessStatuses':dict(Counter(s['ridership']['status'] for s in merged)),
        'economicAvailableStations':sum(bool(merged_contexts[s['meshCode']]['economicComponents']) for s in merged),
        'populationAvailableStations':sum(bool(merged_contexts[s['meshCode']]['populationComponents']) for s in merged)}
    output={'version':'1.0.0','generatedAt':datetime.now(timezone.utc).isoformat(),'scope':scope,'coverage':coverage,
        'baseDataSha256':hashlib.sha256((ROOT/'dist/data.json').read_bytes()).hexdigest(),
        'stations':sorted(stations,key=lambda s:s['id']),'stationMemberships':memberships,
        'officialRoutes':sorted(routes.values(),key=lambda r:(r['operator'],r['name'])),'meshContexts':contexts,
        'studentMeshContexts':students,'studentSources':json.loads((ROOT/'dist/students.json').read_text())['sources'],
        'sources':base['sources'],'sourceArtifacts':[{'id':a['artifact_id'],'sha256':a['sha256'],'url':a['url'],
            'referencePeriod':str(a['reference_date_or_period']),'published':str(a['publication_date_or_period'])}
            for a in artifacts if a['source_id'] in {'ksj_n02_2025','ksj_s12_2024','estat_economic_census_mesh_2021','estat_population_census_mesh_2020'}]}
    registry_path.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'dist/network.json').write_text(json.dumps(output,ensure_ascii=False,separators=(',',':'))+'\n')
    (ROOT/'data/manifests/network_identity.json').write_text(json.dumps({'scopeVersion':scope['version'],'coverage':coverage,'records':audit,'unresolved':unresolved},ensure_ascii=False,separators=(',',':'))+'\n')
    print(json.dumps(coverage,ensure_ascii=False))


if __name__=='__main__': main()
