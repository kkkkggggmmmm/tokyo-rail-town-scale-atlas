#!/usr/bin/env python3
"""Build a public pilot data extract from validated G2/G3 and locked raw archives.

No network requests, rankings, center estimates, prefecture rollups, or S12 sums.
Run with atlas-deps on PYTHONPATH and --root pointing to the canonical checkout.
"""
from __future__ import annotations
import argparse
from collections import defaultdict, Counter
from datetime import datetime, timezone
import hashlib
import importlib
import json
import math
from pathlib import Path
import sys
from zipfile import ZipFile

PUBLIC_PREFECTURES = {'11', '12', '13', '14'}
METRICS = {'restaurants': 'T001163082', 'retail': 'T001163062', 'employees': 'T001163108', 'apparel': 'T001163064'}

def mesh_code(lon, lat):
    """Inverse of the existing normalizer's fourth-level mesh bounds."""
    south = math.floor(lat * 240 + 1e-8)
    west = math.floor((lon - 100) * 160 + 1e-8)
    p, y = divmod(south, 160)
    q, x = divmod(west, 160)
    a, y = divmod(y, 20)
    b, x = divmod(x, 20)
    c, y = divmod(y, 2)
    d, x = divmod(x, 2)
    return f'{p:02}{q:02}{a}{b}{c}{d}{1 + x + 2*y}'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1]/'dist/data.json')
    parser.add_argument('--omit-rail-geometry', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    sys.path.insert(0, str(root))
    import pyarrow.parquet as pq
    import yaml
    normalizer = importlib.import_module('scripts.normalize_phase1_g3')
    normalizer.ROOT = root
    semantics = importlib.import_module('scripts.observation_semantics')
    def read(name, **kwargs):
        return pq.read_table(root / f'data/derived/{name}.parquet', **kwargs).to_pylist()
    all_stations = {r['station_id']: r for r in read('stations')}
    all_lines = read('lines')
    crosswalk = read('station_line_crosswalk')
    # G2 locks the full TX validation corridor. Only its first 14 stations are
    # public; assert the named border station instead of inferring a bbox prefecture.
    tx = sorted((r for r in crosswalk if r['pilot_corridor_id'] == 'pc_tsukuba_express'), key=lambda r:r['sequence_index'])
    cutoff = next(r['sequence_index'] for r in tx if all_stations[r['station_id']]['display_name_ja'] == '柏たなか')
    assert cutoff == 14
    crosswalk = [r for r in crosswalk if r['pilot_corridor_id'] != 'pc_tsukuba_express' or r['sequence_index'] <= cutoff]
    selected_ids = {r['station_id'] for r in crosswalk}
    by_station, by_route = defaultdict(list), defaultdict(list)
    for r in crosswalk:
        by_station[r['station_id']].append(r)
        by_route[r['pilot_corridor_id']].append(r)
    lock = yaml.safe_load((root/'data/manifests/source_lock.phase1.yml').read_text())
    artifacts = {r['artifact_id']:r for r in lock['artifacts']}
    n02 = next(r for r in artifacts.values() if r['source_id'] == 'ksj_n02_2025')
    with ZipFile(root/n02['local_path']) as z:
        station_features = json.loads(z.read('N02-25_GML/UTF-8/N02-25_Station.geojson'))['features']
        rail_features = json.loads(z.read('N02-25_GML/UTF-8/N02-25_RailroadSection.geojson'))['features']
    # Full N02 group membership includes official routes outside the pilot.
    # A route is the pair (operator, official N02 route), never a service name.
    source_groups = defaultdict(set)
    for f in station_features:
        p = f['properties']
        source_groups[str(p['N02_005g'])].add((p['N02_004'],p['N02_003']))
    observations = defaultdict(dict)
    for r in read('station_access_observations'):
        if r['station_id'] in selected_ids:
            # Same source feature is copied for multiple pilot memberships in G3.
            observations[r['station_id']][r['source_record_key']] = r
    colors = {k:{'color':v} for k,v in {'pc_jr_chuo_rapid':'#be6133','pc_jr_sobu_local':'#a88623','pc_jr_keihin_tohoku_negishi':'#318298','pc_tokyu_toyoko':'#b84c5a','pc_odakyu_odawara':'#3972a6','pc_tobu_tojo':'#705b99','pc_tokyo_metro_ginza':'#c8872a','pc_tsukuba_express':'#367963'}.items()}
    routes=[]
    for line in all_lines:
        rid=line['pilot_corridor_id']; ordered=sorted(by_route[rid],key=lambda r:r['sequence_index'])
        route_keys=sorted({(r['n02_operator_key'],r['n02_route_key']) for r in ordered})
        routes.append({'id':rid,'lineId':line['line_id'],'name':line['display_name_ja'],
            'shortName':colors.get(rid,{}).get('shortName',line['display_name_ja']),
            'color':colors.get(rid,{}).get('color','#617385'),'start':all_stations[ordered[0]['station_id']]['display_name_ja'],
            'end':all_stations[ordered[-1]['station_id']]['display_name_ja'],
            'stationIds':[r['station_id'] for r in ordered], 'stationCount':len(ordered),
            'officialRouteKeys':[{'operator':op,'route':route}for op,route in route_keys],
            'scope':'G2確定区間。TXは柏たなかまで。運行系統とN02上の正式路線は区別する。'})
    stations=[]
    for sid in sorted(selected_ids):
        s=all_stations[sid]; memberships=by_station[sid]
        lon,lat=float(s['centroid_lon']),float(s['centroid_lat'])
        mc=mesh_code(lon,lat); b=normalizer.mesh_500m_bounds(mc)
        assert b[0]<=lon<b[2] and b[1]<=lat<b[3], (sid,mc)
        obs=sorted(observations[sid].values(),key=lambda r:r['source_record_key'])
        eligible=[o for o in obs if o['observation_status'] in ('observed','observed_zero')]
        # Only select a single authoritative feature. Never sum source features;
        # multiple numeric records remain unresolved even when numerically equal.
        chosen=eligible[0] if len(eligible)==1 else None
        status=chosen['observation_status'] if chosen else ('ambiguous_multiple_records' if len(eligible)>1 else (obs[0]['observation_status'] if obs and len({o['observation_status'] for o in obs})==1 else 'source_absent'))
        group_routes=sorted(source_groups[str(s['n02_station_group_key'])])
        compact_obs=[{'value':o['numeric_value'],'raw':o['raw_value'],'status':o['observation_status'],
            'sourceKey':o['s12_source_key'],'sourceRecordKey':o['source_record_key'],'duplicateCode':o['s12_duplicate_code'],
            'existenceCode':o['s12_existence_code'],'note':o['s12_note']} for o in obs]
        station={'id':sid,'groupId':memberships[0]['station_group_id'],'name':s['display_name_ja'],
            'operator':s['operator_id'],'coordinates':[round(lon,7),round(lat,7)],'coordinateCRS':s['geometry_crs'],
            'routeIds':sorted({r['pilot_corridor_id'] for r in memberships}),
            'routePositions':{r['pilot_corridor_id']:r['sequence_index'] for r in memberships},
            'sourceStationGroupKey':s['n02_station_group_key'],'officialRouteCount':len(group_routes),
            'officialRouteMemberships':[{'operator':op,'route':route}for op,route in group_routes],
            'officialRouteCountLabel':'N02の同一駅群に属する正式路線数（運行系統数ではない）',
            'ridership':{'fiscalYear':2024,'value':chosen['numeric_value'] if chosen else None,'status':status,
                'measureLabel':'S12掲載の1日当たり駅別乗降客数','unit':'人/日','sourceId':'s12',
                'selection':'single_observed_source_feature' if chosen else 'no_unambiguous_observed_feature',
                'note':chosen['s12_note'] if chosen else None,'observations':compact_obs,
                'hasDuplicateRecords':any(o['s12_duplicate_code']=='2' for o in obs),'summationAllowed':False},'meshCode':mc}
        # N02 has no explicit administrative prefecture field. Omit station
        # prefecture rather than deriving it from bounding boxes or mesh files.
        stations.append(station)
    wanted={s['meshCode'] for s in stations}
    contexts={m:{'bounds':list(normalizer.mesh_500m_bounds(m)),'economicComponents':[], 'populationComponents':[],
        'label':'駅の座標を含む500m区画・都県公表分','fullMeshRollup':False}for m in sorted(wanted)}
    econ_meta=read('economic_mesh_500m',filters=[('mesh_code','in',sorted(wanted))])
    meta={(r['prefecture_partition_code'],r['mesh_code']):r for r in econ_meta}
    used_artifacts={n02['artifact_id']}
    for a in artifacts.values():
        if a['source_id']!='estat_economic_census_mesh_2021' or str(a['prefecture_code']) not in PUBLIC_PREFECTURES:continue
        pref=str(a['prefecture_code']);used_artifacts.add(a['artifact_id'])
        for row_number,raw in normalizer.estat_rows(a):
            m=raw['KEY_CODE'].strip()
            if m not in wanted:continue
            component={'prefectureCode':pref,'sourceArtifactId':a['artifact_id'],'sourceRowNumber':row_number,
                'observationId':f'economic-2021:{pref}:{m}','referenceDate':'2021-06-01'}
            for name,column in METRICS.items():
                o=semantics.normalize_estat_count(raw[column])
                component[name]={'value':normalizer.int_or_none(o.numeric_value),'raw':o.raw_value,'status':o.status}
            mr=meta[(pref,m)];component['sourcePartitionCodes']=json.loads(mr['mesh_partition_codes_json'])
            component['rollupStatus']=mr['cross_partition_rollup_status']
            contexts[m]['economicComponents'].append(component)
    for r in read('population_mesh_500m',filters=[('mesh_code','in',sorted(wanted))]):
        if r['prefecture_partition_code'] not in PUBLIC_PREFECTURES:continue
        used_artifacts.add(r['source_artifact_id'])
        contexts[r['mesh_code']]['populationComponents'].append({'prefectureCode':r['prefecture_partition_code'],
            'observationId':r['mesh_partition_observation_id'],'referenceDate':'2020-10-01',
            'value':r['resident_population_value'],'raw':r['resident_population_raw'],'status':r['resident_population_status'],
            'processingCode':r['suppression_processing_code'],'aggregationTarget':r['aggregation_destination_mesh_code'],
            'aggregatedSourceMeshCodes':r['aggregated_source_mesh_codes'],'sourcePartitionCodes':json.loads(r['mesh_partition_codes_json']),
            'rollupStatus':r['cross_partition_rollup_status'],'sourceArtifactId':r['source_artifact_id']})
    for c in contexts.values():
        for key in ('economicComponents','populationComponents'):
            c[key].sort(key=lambda r:r['prefectureCode'])
        c['economicStatus']='available' if c['economicComponents'] else 'source_absent'
        c['populationStatus']='available' if c['populationComponents'] else 'source_absent'
        c['outsidePublicComponentCodes']=sorted({p for rows in (c['economicComponents'],c['populationComponents'])for r in rows for p in r['sourcePartitionCodes'] if p not in PUBLIC_PREFECTURES})
    access_artifact=next(r for r in artifacts.values() if r['source_release_id']=='S12-25');used_artifacts.add(access_artifact['artifact_id'])
    sources=[{'id':'n02','title':'国土数値情報 鉄道データ N02-25','referenceDate':'2025-12-31','published':'2026-04',
        'url':'https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N02-2025.html','termsUrl':'https://nlftp.mlit.go.jp/ksj/other/agreement_01.html'},
        {'id':'s12','title':'国土数値情報 駅別乗降客数 S12-25','referencePeriod':'FY2024','published':'2026-04',
        'url':'https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-S12-2024.html','termsUrl':'https://nlftp.mlit.go.jp/ksj/other/agreement_01.html',
        'valueField':'S12_061','note':'事業者原表と集計範囲・乗車/乗降の扱いが異なる。JR原表の乗車のみの値と同一視しない。重複コード2は欠測状態として保持し、駅・路線・事業者間の合計を作らない。'},
        {'id':'economic','title':'令和3年経済センサス 500mメッシュ T001163','referenceDate':'2021-06-01',
        'url':'https://www.stat.go.jp/data/mesh/r3_w.html','definitionUrl':'https://www.e-stat.go.jp/help/data-definition-information/downloaddata/T001163.pdf',
        'termsUrl':'https://www.e-stat.go.jp/terms-of-use','metrics':METRICS,
        'labels':{'restaurants':'飲食店事業所数（76飲食店）','retail':'小売業事業所数','employees':'全産業従業者数','apparel':'織物・衣服・身の回り品小売業事業所数'},
        'note':'飲食店はT001163082。宿泊業・飲食サービス業合計の080は使用しない。'},
        {'id':'population','title':'令和2年国勢調査 500mメッシュ T001141','referenceDate':'2020-10-01',
        'url':'https://www.stat.go.jp/data/mesh/r2_w.html','definitionUrl':'https://www.e-stat.go.jp/help/data-definition-information/downloaddata/T001141.pdf',
        'termsUrl':'https://www.e-stat.go.jp/terms-of-use','note':'秘匿・合算先を保持。合算先の人口を当該単一区画だけの人口と扱わない。'}]
    output={'version':'1.0.0','generatedAt':datetime.now(timezone.utc).isoformat(),'scope':{'prefectureCodes':sorted(PUBLIC_PREFECTURES),
        'txEnd':'柏たなか','stationSelection':'G2確定8区間の駅。TX茨城6駅と分析専用補助駅を除外。',
        'meshSelection':'駅代表座標を含む公式500m区画。1都3県の公表成分を別々に保持。',
        'centerEstimates':False,'wholeMeshRollups':False,'ridershipSummation':False},'sources':sources,'routes':routes,'stations':stations,'meshContexts':contexts,
        'sourceArtifacts':[{'id':a['artifact_id'],'release':a['source_release_id'],'sha256':a['sha256'],'url':a['url'],
            'referencePeriod':str(a['reference_date_or_period']),'published':str(a['publication_date_or_period'])}for a in artifacts.values() if a['artifact_id'] in used_artifacts],
        'derivedInputHashes':{n:digest(root/f'data/derived/{n}.parquet') for n in ['stations','lines','station_line_crosswalk','station_access_observations','population_mesh_500m','economic_mesh_500m']}}
    if not args.omit_rail_geometry:
        from shapely.geometry import box, shape, mapping
        from shapely.ops import unary_union
        route_boxes={}
        for route in routes:
            pts=[all_stations[sid] for sid in route['stationIds']]
            clip=box(min(s['centroid_lon'] for s in pts)-.003,min(s['centroid_lat'] for s in pts)-.003,
                max(s['centroid_lon'] for s in pts)+.003,max(s['centroid_lat'] for s in pts)+.003)
            route_boxes[route['id']]=(clip,{(r['operator'],r['route'])for r in route['officialRouteKeys']})
        features=[]
        for index,f in enumerate(rail_features,1):
            p=f['properties']; key=(p['N02_004'],p['N02_003']); matching=[(rid,b)for rid,(b,keys)in route_boxes.items() if key in keys]
            if not matching:continue
            g=shape(f['geometry']); relevant=[(rid,b)for rid,b in matching if g.intersects(b)]
            if not relevant:continue
            clipped=g.intersection(unary_union([b for _,b in relevant]))
            if clipped.is_empty or clipped.geom_type not in ('LineString','MultiLineString'):continue
            features.append({'type':'Feature','properties':{'sourceFeatureIndex':index,'operator':key[0],'officialRoute':key[1],
                'pilotRouteIds':[rid for rid,_ in relevant]},'geometry':mapping(clipped)})
        output['railGeometry']={'type':'FeatureCollection','features':features}
        output['railGeometryMetadata']={'sourceId':'n02','label':'N02正式路線の実形状・参考範囲',
            'clipMethod':'正式路線名と事業者で抽出し、各公開区間の駅代表点を囲む矩形に0.003度余白を足して切り出す。',
            'caution':'矩形内の枝線・区間外部分を含み得る参考地図。運行系統の厳密な区間線ではない。駅間直線による補間なし。'}
    output['coverage']={'stationCount':len(stations),'routeCount':len(routes),'meshCount':len(contexts),
        'accessStatuses':dict(Counter(s['ridership']['status']for s in stations)),
        'economicComponents':sum(len(c['economicComponents'])for c in contexts.values()),
        'populationComponents':sum(len(c['populationComponents'])for c in contexts.values())}
    assert len(routes)==8 and all(s['name'] not in {'守谷','みらい平','みどりの','万博記念公園','研究学園','つくば'} for s in stations)
    assert all(c['prefectureCode'] in PUBLIC_PREFECTURES for m in contexts.values()for key in ['economicComponents','populationComponents']for c in m[key])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(output,ensure_ascii=False,separators=(',',':'))+'\n')
    print(json.dumps({'output':str(args.output),'bytes':args.output.stat().st_size,**output['coverage']},ensure_ascii=False))
if __name__=='__main__':
    main()
