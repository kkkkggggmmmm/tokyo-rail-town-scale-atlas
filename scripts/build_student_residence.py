"""Build a research asset from official 2020 Census 500m prefecture partitions.
Preserve prefecture components and original suppression/aggregation metadata.
"""
from pathlib import Path
import csv,io,json,zipfile,hashlib,sys,collections
REPO=Path(__file__).resolve().parents[1]
BASE=REPO/'data/raw/supplements/student'
META=REPO/'data/reference/quantitative/student'
sys.path.insert(0,str(REPO/'scripts'))
from observation_semantics import normalize_census_count
FIELDS={'university':'T001144046','juniorCollege':'T001144043','highSchool':'T001144040','allStudents':'T001144034'}
existing=json.loads((REPO/'dist/data.json').read_text())
contexts={code:{'components':[]} for code in sorted(existing['meshContexts'])}
sources=[]
for pref in ['11','12','13','14']:
 p=BASE/f'census-2020-T001144-H-{pref}.zip'
 meta=json.loads((META/f'source-{pref}.json').read_text())
 assert hashlib.sha256(p.read_bytes()).hexdigest()==meta['sha256']
 sid=f'estat-census-2020-student-500m-jgd2011-{pref}'
 sources.append({'id':sid,'tableId':'T001144','title':'2020年国勢調査 地域メッシュ・人口移動、就業状態等及び従業地・通学地','prefectureCode':pref,'url':meta['url'],'termsUrl':'https://www.e-stat.go.jp/terms-of-use','license':'e-Stat terms; CC BY 4.0 compatible','definitionUrl':'https://www.e-stat.go.jp/help/data-definition-information/downloaddata/T001144.pdf','referenceDate':'2020-10-01','publicationDate':None,'publicationDateStatus':'table_specific_date_not_confirmed','seriesAnnouncementDate':'2022-07-27','seriesAnnouncementUrl':'https://www.stat.go.jp/data/mesh/r2_w.html','distributionPeriod':'2025-10','distributionEvidenceUrl':'https://www.e-stat.go.jp/help/data-definition-information/download','retrievedAt':meta['retrieved_at'],'sha256':meta['sha256'],'byteSize':meta['byte_size'],'sourceRowCount':meta['row_count'],'memberName':f'tblT001144H{pref}.txt','aggregationUnit':'500m mesh prefecture component','crs':'EPSG:6668'})
 with zipfile.ZipFile(p) as z:
  r=csv.DictReader(io.StringIO(z.read(f'tblT001144H{pref}.txt').decode('cp932')))
  headers=next(r)
  for key,col in FIELDS.items():assert col in headers
  for number,row in enumerate(r,start=3):
   code=row['KEY_CODE']
   if code not in contexts:continue
   item={'prefectureCode':pref,'sourceId':sid,'sourceRowNumber':number,'referenceDate':'2020-10-01','processingCode':row['HTKSYORI'],'aggregationTarget':row['HTKSAKI'] or None,'aggregatedSourceMeshCodes':row['GASSAN'] or None,'rawProcessing':{k:row[k] for k in ['KEY_CODE','HTKSYORI','HTKSAKI','GASSAN']},'sourcePartitionCodes':sorted({pref}|{p for c in existing['meshContexts'][code]['populationComponents'] for p in c['sourcePartitionCodes']})}
   for key,col in FIELDS.items():
    x=normalize_census_count(row[col],suppression_processing_code=row['HTKSYORI'])
    item[key]={'value':int(x.numeric_value) if x.numeric_value is not None else None,'raw':x.raw_value,'status':x.status,'column':col}
   contexts[code]['components'].append(item)
for code,ctx in contexts.items():
 ctx['status']='available' if ctx['components'] else 'source_absent'
 ctx['sourcePartitionCodes']=[x['prefectureCode'] for x in ctx['components']]
 ctx['fullMeshRollup']=False
asset={'version':'student-residence-v1','scope':'Existing public station 500m mesh codes; 11-14 prefecture components only','sources':sources,'metrics':{'university':{'label':'大学・大学院の在学者（居住者）','unit':'人','column':'T001144046'},'juniorCollege':{'label':'短大・高専の在学者（居住者）','unit':'人','column':'T001144043'},'highSchool':{'label':'高校の在学者（居住者）','unit':'人','column':'T001144040'},'allStudents':{'label':'在学者総数（居住者）','unit':'人','column':'T001144034'}},'interpretation':{'residenceNotAttendance':True,'commutingInflowAvailable':False,'definitionNote':'国勢調査の学校区分による。大学・大学院には相当する教育課程を含み、定時制・通信制も含む。一部の専修学校・各種学校は入学資格・修業年数により大学・短大・高専等に分類される。','definitionUrl':'https://www.stat.go.jp/data/kokusei/2020/kekka/pdf/ug_03.pdf','ratioRule':'分母は同じ2020-10-01・同じmesh・同じprefectureの人口。双方processingCode=0かつ数値公表のみ。総人口0の場合は算出不可。秘匿・合算・府県またぎ未集計を0にしない。'},'meshContexts':contexts,'coverage':{'targetMeshCount':len(contexts),'withComponents':sum(bool(c['components']) for c in contexts.values()),'componentCount':sum(len(c['components']) for c in contexts.values()),'processingCodes':dict(collections.Counter(x['processingCode'] for c in contexts.values() for x in c['components']))}}
(REPO/'dist/students.json').write_text(json.dumps(asset,ensure_ascii=False,separators=(',',':'))+'\n')
print(json.dumps(asset['coverage'],ensure_ascii=False))
print('OUTPUT',REPO/'dist/students.json')
