import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import {studentCount,studentShare,filterDistricts,districtTotal,moneyLabel} from '../dist/supplements.mjs';
import {studentSection,districtRows,cafeRows} from '../dist/supplement-views.mjs';
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
