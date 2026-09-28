from pathlib import Path
import json,re,hashlib,datetime,html,collections
repo=Path(__file__).resolve().parents[1]
root=repo/'data/raw/supplements'
meta=repo/'data/reference/quantitative'
x=json.loads((root/'cafe_result.json').read_text());request=json.loads((meta/'cafe_request.json').read_text())
rows=[]
for code,name,raw in re.findall(r'<th[^>]+data-unique="([0-9]{5})"[^>]*>\s*([^<]+)\s*</th>\s*<td[^>]*>\s*([^<]+)\s*</td>',x['table']):
 raw=html.unescape(raw).strip();name=html.unescape(name).strip()
 val=int(raw.replace(',','')) if re.fullmatch(r'[0-9,]+',raw) else None
 rows.append({'area_code':code,'area_name':name,'scope':'municipality_or_designated_city_ward','metric':'cafe_establishments','value':val,'raw_value':raw,'status':'observed' if val is not None else 'symbol_unresolved','unit':'事業所','reference_date':'2021-06-01','industry_code':'767','organization_code':'1','employee_size_code':'00','source_id':'estat_econ2021_table9_3_cafes','approved_for_display':val is not None})
assert len(rows)==258 and len({r['area_code'] for r in rows})==258
assert set(r['area_code'] for r in rows)==set(v['code'] for v in request['rows'][0]['listData'])
assert x['moveData']=={'rightMoveFlg':0,'underMoveFlg':0,'leftMoveFlg':0,'upMoveFlg':0}
by={r['area_code']:r for r in rows}
checks=[]
for city,wards in [('11100',range(11101,11111)),('12100',range(12101,12107)),('14100',range(14101,14119)),('14130',range(14131,14138)),('14150',range(14151,14154))]:
 actual=by[city]['value'];s=sum(by[str(w)]['value'] for w in wards);assert actual==s;checks.append({'city':by[city]['area_name'],'official_total':actual,'sum_of_wards':s,'pass':True})
source=json.loads((meta/'cafe_source.json').read_text())
assert source['response_sha256']==hashlib.sha256((root/'cafe_result.json').read_bytes()).hexdigest()
out={'source':source,'observations':rows,'qa':{'requested_rows':258,'received_rows':len(rows),'unique_area_codes':258,'statuses':dict(collections.Counter(r['status'] for r in rows)),'sum_checks':checks,'repair_attempts':0,'failure_log':[{'target':'web open dbview 0004005673','result':'response too large >4MiB','replacement':'local official HTTP GET succeeded once'}]}}
(repo/'dist/cafes.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'))+'\n')
for name in ['新宿区','渋谷区','豊島区','千代田区','武蔵野市','立川市','八王子市','横浜市','川崎市','さいたま市','川越市','船橋市','千葉市','柏市']:
 r=next(r for r in rows if r['area_name']==name);print(name,r['value'])
print('QA',out['qa'])
