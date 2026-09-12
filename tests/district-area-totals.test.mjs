import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import {DISTRICT_AREAS,aggregateArea,rankAreas} from '../dist/district-areas.mjs';

const asset=JSON.parse(readFileSync(new URL('../dist/commercial-districts.json',import.meta.url)));
const retail='retail_sales_million_yen';
const food='food_service_sales_million_yen';
const personal='personal_service_sales_million_yen';
const floor='retail_sales_floor_sqm';
const keys=[retail,food,personal,floor,'total'];
const area=(id,sourceDistrictIds)=>({id,name:id,sourceDistrictIds,aggregationAllowed:false,selectedDistrictSumAllowed:true});
const district=(id,value,status='observed')=>({
 source_district_id:id,name:id,prefecture_code:'13',municipality_name:'検証用市',
 metrics:Object.fromEntries([retail,food,personal,floor].map(key=>[key,{value,status,raw:value}]))
});

test('eight frozen area rosters reproduce published-district sums without changing source observations',()=>{
 const before=JSON.stringify(asset),rostersBefore=JSON.stringify(DISTRICT_AREAS);
 const expected={新宿:956086,銀座:882987,渋谷:614511,池袋:604339,'原宿・表参道':489112,日本橋:330422,六本木:292558,吉祥寺:160354};
 const completePersonal=new Set(['新宿','日本橋','原宿・表参道','吉祥寺']);
 assert.equal(DISTRICT_AREAS.length,8);
 for(const a of DISTRICT_AREAS){
  assert.equal(a.aggregationAllowed,false,'a sum of listed districts must not approve a canonical center boundary');
  assert.equal(a.selectedDistrictSumAllowed,true);
  const result=aggregateArea(asset,a),n=a.sourceDistrictIds.length;
  assert.equal(result.identityValid,true);
  assert.equal(result.districts.length,n);
  assert.equal(result.metrics[retail].value,expected[a.name]);
  for(const key of [retail,food,floor]){
   const m=result.metrics[key];
   assert.equal(m.complete,true);assert.equal(m.expected,n);assert.equal(m.observed,n);assert.deepEqual(m.missing,[]);
   const direct=asset.districts.filter(d=>a.sourceDistrictIds.includes(d.source_district_id)).reduce((sum,d)=>sum+d.metrics[key].value,0);
   assert.equal(m.value,direct);
  }
  assert.equal(result.metrics[personal].complete,completePersonal.has(a.name));
  assert.equal(result.metrics.total.complete,completePersonal.has(a.name));
  assert.equal(result.metrics.total.expected,3*n);
  if(completePersonal.has(a.name)){
   assert.equal(result.metrics.total.value,[retail,food,personal].reduce((sum,key)=>sum+result.metrics[key].value,0));
  }else{
   assert.equal(result.metrics[personal].value,null);assert.equal(result.metrics.total.value,null);
   assert.ok(result.metrics[personal].missing.length>0);
  }
 }
 assert.equal(JSON.stringify(asset),before);assert.equal(JSON.stringify(DISTRICT_AREAS),rostersBefore);
});

test('retail ranks cover all eight groups and incomplete three-sector sums receive no rank',()=>{
 const r=rankAreas(asset);
 assert.equal(r.sort,retail);assert.equal(r.eligible,8);
 assert.deepEqual(r.rows.map(r=>r.area.name),['新宿','銀座','渋谷','池袋','原宿・表参道','日本橋','六本木','吉祥寺']);
 assert.deepEqual(r.rows.map(r=>r.rank),[1,2,3,4,5,6,7,8]);
 for(const dir of ['asc','desc']){
  const total=rankAreas(asset,{sort:'total',dir});
  assert.equal(total.eligible,4);assert.equal(total.rows.length,8);
  assert.ok(total.rows.slice(0,4).every(r=>Number.isFinite(r.value)&&r.rank!==null));
  assert.ok(total.rows.slice(4).every(r=>r.value===null&&r.rank===null));
 }
 for(const sort of [food,floor])assert.equal(rankAreas(asset,{sort}).eligible,8);
});

test('a child-name search selects its complete area roster rather than summing only the matched child',()=>{
 const r=rankAreas(asset,{query:'サンシャイン',prefecture:'13'});
 assert.equal(r.rows.length,1);assert.equal(r.rows[0].area.name,'池袋');
 assert.equal(r.rows[0].districts.length,7);assert.equal(r.rows[0].value,604339);
 assert.equal(r.rows[0].metrics[retail].expected,7);
 assert.equal(rankAreas(asset,{prefecture:'14'}).rows.length,0);
 assert.equal(rankAreas(asset,{query:'該当しない街'}).rows.length,0);
});

test('suppression and missing tokens block only affected sums and retain auditable missing-component identities',()=>{
 for(const status of ['suppressed','not_applicable','not_acquired']){
  const first=district('a',10),second=district('b',20);
  second.metrics[personal]={value:999,status,raw:status==='suppressed'?'x':'-'};
  const r=aggregateArea({districts:[first,second]},area('test',['a','b']));
  assert.equal(r.identityValid,true);assert.equal(r.metrics[retail].value,30);
  assert.equal(r.metrics[personal].value,null);assert.equal(r.metrics[personal].complete,false);
  assert.equal(r.metrics[personal].observed,1);assert.equal(r.metrics[personal].expected,2);
  assert.deepEqual(r.metrics[personal].missing,[{districtId:'b',name:'b',metric:personal,status}]);
  assert.equal(r.metrics.total.value,null);assert.equal(r.metrics.total.observed,5);assert.equal(r.metrics.total.expected,6);
 }
 const absent=district('a',5);delete absent.metrics[food];
 const r=aggregateArea({districts:[absent]},area('test',['a']));
 assert.equal(r.metrics[food].value,null);assert.equal(r.metrics.total.value,null);
 assert.equal(r.metrics[food].missing[0].districtId,'a');assert.equal(r.metrics[food].missing[0].metric,food);
});

test('numeric zero and rounded observations remain distinguishable from unavailable and non-finite values',()=>{
 for(const status of ['observed','observed_zero','below_rounding_unit']){
  const r=aggregateArea({districts:[district('a',0,status)]},area('test',['a']));
  assert.equal(r.metrics[retail].value,0);assert.equal(r.metrics[retail].complete,true);
  assert.equal(r.metrics[retail].rounded,status==='below_rounding_unit');
  assert.equal(r.metrics.total.value,0);assert.equal(r.metrics.total.rounded,status==='below_rounding_unit');
 }
 for(const value of [null,undefined,NaN,Infinity,'12']){
  const r=aggregateArea({districts:[district('a',value)]},area('test',['a']));
  assert.equal(r.metrics[retail].value,null);assert.equal(r.metrics.total.value,null);
  assert.equal(r.metrics[retail].complete,false);
 }
 const r=aggregateArea({districts:[district('a',0,'below_rounding_unit'),district('b',8)]},area('test',['a','b']));
 assert.equal(r.metrics[retail].value,8);assert.equal(r.metrics[retail].rounded,true);
});

test('unresolved or duplicate source identities fail closed instead of inflating or shrinking sums',()=>{
 const fixtures=[
  [{districts:[district('a',10)]},area('unknown',['a','missing'])],
  [{districts:[district('a',10)]},area('duplicate-roster',['a','a'])],
  [{districts:[district('a',10),district('a',20)]},area('duplicate-source',['a'])],
  [{districts:[district('a',10)]},area('empty',[])]
 ];
 for(const [source,a] of fixtures){
  const r=aggregateArea(source,a);assert.equal(r.identityValid,false,a.id);
  for(const key of keys){assert.equal(r.metrics[key].value,null,a.id+':'+key);assert.equal(r.metrics[key].complete,false);}
  const ranked=rankAreas(source,{areas:[a]});assert.equal(ranked.eligible,0);assert.equal(ranked.rows[0].rank,null);
 }
});

test('a source district assigned to two requested groups blocks both groups but preserves disjoint groups',()=>{
 const source={districts:[district('a',10),district('b',20),district('c',30)]};
 const areas=[area('first',['a','b']),area('overlap',['b']),area('disjoint',['c'])];
 const ranked=rankAreas(source,{areas});
 assert.equal(ranked.eligible,1);assert.equal(ranked.rows[0].area.name,'disjoint');assert.equal(ranked.rows[0].value,30);
 for(const r of ranked.rows.slice(1)){
  assert.equal(r.identityValid,false);assert.equal(r.value,null);assert.equal(r.rank,null);
  for(const key of keys)assert.equal(r.metrics[key].value,null);
 }
});

test('ties use competition ranks and unavailable groups remain last in both directions',()=>{
 const source={districts:[district('a',20),district('b',20),district('c',5),district('d',999,'suppressed'),district('e',0,'observed_zero')]};
 const areas=source.districts.map(d=>area(d.name,[d.source_district_id]));
 const before=JSON.stringify({source,areas});
 const desc=rankAreas(source,{areas});
 assert.deepEqual(desc.rows.map(r=>r.area.name),['a','b','c','e','d']);
 assert.deepEqual(desc.rows.map(r=>r.rank),[1,1,3,4,null]);
 const asc=rankAreas(source,{areas,dir:'asc'});
 assert.deepEqual(asc.rows.map(r=>r.area.name),['e','c','a','b','d']);
 assert.deepEqual(asc.rows.map(r=>r.rank),[1,2,3,3,null]);
 assert.equal(desc.eligible,4);assert.equal(asc.eligible,4);
 assert.equal(JSON.stringify({source,areas}),before);
});
