import {DISTRICT_AREAS,areaDistricts,filterAreas} from '../dist/district-areas.mjs';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import {studentCount,studentShare,filterDistricts,districtTotal,moneyLabel,DISTRICT_METRICS,rankDistricts,districtSortPatch} from '../dist/supplements.mjs';
import {studentSection,districtView,districtRows,districtAreaView,cafeRows} from '../dist/supplement-views.mjs';
import {parseExplorerState,serializeExplorerState} from '../dist/explorer-model.mjs';
import {evaluateRoutes,routeCsv,parseState} from '../dist/app.mjs';
const load=name=>JSON.parse(readFileSync(new URL('../dist/'+name,import.meta.url)));
const data=load('data.json'),students=load('students.json'),districts=load('commercial-districts.json'),cafes=load('cafes.json');
const station=data.stations.find(s=>s.name==='東海大学前');

test('resident student numbers and denominator reproduce official observed counts',()=>{
 assert.equal(studentCount(students,station),350);
 assert.equal(studentShare(data,students,station),350/1882*100);
 const west=data.stations.find(s=>s.name==='西千葉');
 assert.equal(studentCount(students,west),367);
 assert.equal(studentShare(data,students,west),367/2895*100);
 const html=studentSection(data,students,station);
 assert.ok(html.includes('350'));assert.ok(html.includes('18.6'));
 assert.ok(html.includes('2020年10月1日'));assert.ok(html.includes('通ってくる学生数は含みません'));
});
test('student share rejects suppression, aggregation, partition, date and denominator mismatches',()=>{
 const changes=[(c,p)=>{c.university.value=null;c.university.status='suppressed'},(c,p)=>{c.processingCode='1'},(c,p)=>{p.processingCode='1'},(c,p)=>{c.aggregatedSourceMeshCodes='5339'},(c,p)=>{p.aggregationTarget='5339'},(c,p)=>{p.referenceDate='2021-06-01'},(c,p)=>{p.prefectureCode='13'},(c,p)=>{p.sourcePartitionCodes=['14','13']},(c,p)=>{p.value=0},(c,p)=>{c.university.value=p.value+1}];
 for(const change of changes){const d=structuredClone(data),s=structuredClone(students),c=s.meshContexts[station.meshCode].components[0],p=d.meshContexts[station.meshCode].populationComponents[0];change(c,p);assert.equal(studentShare(d,s,station),null);}
 const s=structuredClone(students),c=s.meshContexts[station.meshCode].components[0];c.university={value:0,raw:'0',status:'observed_zero'};assert.equal(studentShare(data,s,station),0);assert.equal(studentCount(s,station),0);
 c.sourcePartitionCodes=['13','14'];assert.equal(studentCount(s,station),null);
});
test('new apparel/student observations do not change the existing three-indicator rank',()=>{
 const d=structuredClone(data);for(const c of Object.values(d.meshContexts).flatMap(m=>m.economicComponents)){c.apparel.value=999999999;}
 assert.deepEqual(evaluateRoutes(d),evaluateRoutes(data));
 const csv=routeCsv(data,'pc_odakyu_odawara',students);assert.ok(csv.includes('住民に占める割合_%'));assert.ok(csv.includes('2020-10-01'));assert.ok(csv.includes('衣服・身の回り品店数'));
 assert.equal(parseState('#view=numbers&detail=districts',data).detail,'districts');
 assert.equal(parseState('#detail=bad',data).detail,'districts');
});
test('district sales are million-yen observations displayed in 100 million yen, not GDP',()=>{
 const ginza=districts.districts.find(d=>d.name==='銀座地域');assert.equal(districtTotal(ginza),998870);assert.equal(moneyLabel({value:998870,status:'observed'}),'9,988.7');
 const d=structuredClone(ginza);d.metrics.retail_sales_million_yen={value:null,status:'suppressed',raw:'x'};assert.equal(districtTotal(d),null);assert.equal(moneyLabel(d.metrics.retail_sales_million_yen),'秘匿');
 assert.equal(moneyLabel({value:0,status:'below_rounding_unit'}),'単位未満');
 const result=districtRows(districts,{query:'銀座地域'});assert.equal(result.total,2);assert.ok(result.html.includes('山王銀座地域'));assert.ok(result.html.includes('9,988.7'));assert.ok(result.html.includes(ginza.source_district_id));
 const north=filterDistricts(districts.districts,{query:'吉祥寺駅北口',prefecture:'13'});assert.equal(north.length,1);assert.equal(districtTotal(north[0]),145799);
 assert.equal(districtRows(districts,{query:'ない地区名'}).total,0);assert.equal(districtRows(districts,{limit:60}).shown,60);
});
test('cafes preserve municipal scope, unknown rows excluded and paging/counts consistent',()=>{
 assert.equal(cafeRows(cafes,{query:'新宿区'}).total,1);assert.ok(cafeRows(cafes,{query:'新宿区'}).html.includes('448'));
 assert.equal(cafeRows(cafes,{limit:300}).total,252);assert.equal(cafeRows(cafes,{limit:300}).shown,252);
 assert.equal(cafeRows(cafes,{limit:30}).shown,30);assert.equal(cafeRows(cafes,{query:'ない自治体'}).total,0);
 assert.equal(cafes.observations.find(r=>r.area_name==='武蔵野市').value,128);
});

test('district rankings cover the full filtered set before pagination for every numeric column',()=>{
 const before=JSON.stringify(districts);
 for(const sort of Object.keys(DISTRICT_METRICS)){
  const filtered=filterDistricts(districts.districts,{prefecture:'13'});
  const values=filtered.map(d=>sort==='total'?districtTotal(d):d.metrics[sort].value).filter(Number.isFinite);
  for(const dir of ['asc','desc']){
   const options={prefecture:'13',sort,dir},r=rankDistricts(districts.districts,options);
   assert.equal(r.rows.length,filtered.length);assert.equal(r.eligible,values.length);
   assert.equal(r.rows[0].value,dir==='asc'?Math.min(...values):Math.max(...values));
   const first=districtRows(districts,{...options,limit:30}),more=districtRows(districts,{...options,limit:60});
   assert.equal(first.shown,30);assert.equal(more.shown,60);assert.ok(more.html.startsWith(first.html));
   assert.ok(first.html.includes(r.rows[0].district.source_district_id));
   assert.ok(r.rows.slice(r.eligible).every(r=>r.rank===null&&r.value===null));
  }
 }
 assert.equal(JSON.stringify(districts),before);
 const q=rankDistricts(districts.districts,{prefecture:'13',query:'吉祥寺',sort:'total'});
 assert.ok(q.rows.every(r=>r.district.prefecture_code==='13'&&r.district.name.includes('吉祥寺')));
});
test('district ranking retains ties and separates rounded values from missing observations',()=>{
 const make=(id,value,status='observed')=>({name:id,prefecture_code:'13',municipality_name:'市',source_district_id:id,metrics:Object.fromEntries(['retail_sales_million_yen','food_service_sales_million_yen','personal_service_sales_million_yen','retail_sales_floor_sqm'].map(k=>[k,{value,status}]))});
 const rows=[make('first',20),make('suppressed',999,'suppressed'),make('tie',20),make('small',5),make('rounded',0,'below_rounding_unit'),make('missing',null,'not_applicable')];
 const desc=rankDistricts(rows,{sort:'retail_sales_million_yen'}).rows;
 assert.deepEqual(desc.map(r=>r.district.name),['first','tie','small','rounded','suppressed','missing']);
 assert.deepEqual(desc.map(r=>r.rank),[1,1,3,4,null,null]);
 const asc=rankDistricts(rows,{sort:'retail_sales_million_yen',dir:'asc'}).rows;
 assert.deepEqual(asc.map(r=>r.district.name),['rounded','small','first','tie','suppressed','missing']);
 assert.deepEqual(asc.map(r=>r.rank),[1,2,3,3,null,null]);
 assert.ok(districtRows({districts:rows},{sort:'retail_sales_million_yen',dir:'asc'}).html.includes('単位未満'));
 const partial=make('partial',10);partial.metrics.food_service_sales_million_yen={status:'suppressed',value:null};
 assert.equal(rankDistricts([partial],{sort:'total'}).rows[0].rank,null);
 assert.deepEqual(rankDistricts(rows).rows.map(r=>r.district.name),rows.map(r=>r.name));
});
test('district header selection has independent shareable state and accessible active headers',()=>{
 let s=parseExplorerState('#view=numbers&detail=districts&rp=13&rq=吉祥寺&sort=retail',data);
 assert.equal(s.districtSort,'source');
 s={...s,...districtSortPatch(s.districtSort,s.districtDir,'total')};
 assert.equal(s.districtDir,'desc');
 s={...s,...districtSortPatch(s.districtSort,s.districtDir,'total')};
 assert.equal(s.districtDir,'asc');
 const restored=parseExplorerState(serializeExplorerState(s),data);
 assert.deepEqual(restored,s);assert.equal(restored.sort,'retail');assert.equal(restored.regionPref,'13');
 assert.deepEqual(districtSortPatch('total','asc','retail_sales_floor_sqm'),{districtSort:'retail_sales_floor_sqm',districtDir:'desc'});
 for(const key of ['constructor','__proto__','toString','bogus'])assert.equal(parseExplorerState('#dsort='+key+'&ddir=bad',data).districtSort,'source');
 const html=districtView(districts,{sort:'total',dir:'asc'});
 assert.equal((html.match(/class="district-sort"/g)||[]).length,5);
 assert.equal((html.match(/aria-sort="ascending"/g)||[]).length,1);
 assert.ok(html.includes('id="district-sort-total"'));assert.ok(html.includes('3業種売上計を大きい順に並べ替え'));
 assert.ok(districtRows(districts,{query:'ない地区名',sort:'total'}).html.includes('colspan="7"'));
});

test('town navigation preserves source IDs and withholds unverified parent totals',()=>{
 const known=new Set(districts.districts.map(d=>d.source_district_id)),assigned=[];
 for(const area of DISTRICT_AREAS){
  assert.match(area.id,/^browse_[a-f0-9]{32}$/);assert.equal(area.aggregationAllowed,false);
  assert.equal(area.status,'boundary_and_membership_unverified');
  assert.ok(area.sourceDistrictIds.every(id=>known.has(id)));
  assigned.push(...area.sourceDistrictIds);
 }
 assert.equal(new Set(assigned).size,assigned.length);
 const ginza=DISTRICT_AREAS.find(a=>a.name==='銀座');
 assert.ok(areaDistricts(districts,ginza).some(d=>d.source_district_id==='13199002'));
 const shinjuku=DISTRICT_AREAS.find(a=>a.name==='新宿');
 assert.ok(areaDistricts(districts,shinjuku).some(d=>d.municipality_code==='13113'));
 const html=districtAreaView(districts,{areaId:shinjuku.id});
 assert.ok(html.includes('地域合計・順位は未算定'));assert.ok(html.includes('タカシマヤタイムズスクエア'));
 assert.ok(html.includes('新宿駅西口'));assert.ok(html.includes('3,753.39'));
 assert.ok(!html.includes('district-rank'));assert.ok(!html.includes('data-district-sort'));
 assert.equal(filterAreas(districts,{query:'サンシャイン'}).at(0).name,'池袋');
 assert.equal(filterAreas(districts,{prefecture:'14'}).length,0);
 assert.ok(districtAreaView(districts,{prefecture:'14'}).includes('公表地区の全データを見る'));
 const s=parseExplorerState('#view=numbers&dmode=source&area='+shinjuku.id+'&dsort=total',data);
 assert.deepEqual(parseExplorerState(serializeExplorerState(s),data),s);
 assert.equal(parseExplorerState('#view=numbers&area=bad&dmode=bad',data).districtMode,'areas');
 assert.equal(parseExplorerState('#area=bad',data).districtArea,'');
});
