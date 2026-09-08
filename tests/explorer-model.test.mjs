import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import {METRIC_DETAILS,THEMES,stationValue,stationPrefectures,parseExplorerState,serializeExplorerState,filterStations,normalizePins,metricCoverage,missingReason} from '../dist/explorer-model.mjs';
const data=JSON.parse(readFileSync(new URL('../dist/data.json',import.meta.url))),students=JSON.parse(readFileSync(new URL('../dist/students.json',import.meta.url)));
const parse=hash=>parseExplorerState(hash,data);
test('shareable URL round-trips filters, sorting, columns, paging and 4 comparison stations',()=>{
 const state={...parse(''),view:'compare',line:data.routes[0].id,q:'東京 中央',theme:'students',pref:'13',sort:'studentShare',dir:'asc',columns:['studentShare','university','ridership'],panel:'list',page:3,available:true,favorites:true,pins:data.stations.slice(0,4).map(s=>s.id),regionQuery:'銀座',regionPref:'13',station:data.stations[3].id};
 assert.deepEqual(parse(serializeExplorerState(state)),state);
});
test('untrusted URL object prototype keys and unknown IDs cannot create invalid state',()=>{
 for(const key of ['constructor','toString','__proto__']){const s=parse('#theme='+key+'&sort='+key+'&cols='+key+'&pins=bad&view='+key);assert.equal(s.theme,'all');assert.equal(s.sort,'restaurants');assert.deepEqual(s.columns,THEMES.all.columns);assert.deepEqual(s.pins,[]);assert.doesNotThrow(()=>serializeExplorerState(s));}
 assert.equal(parse('#sort=ridership').sort,'restaurants');assert.equal(METRIC_DETAILS.ridership.sortable,false);
});
test('pins deduplicate known records, reject unknown IDs and cap at four',()=>{
 const ids=data.stations.slice(0,6).map(s=>s.id);assert.deepEqual(normalizePins([ids[0],ids[0],'bad',...ids],data),ids.slice(0,4));
});
test('search, line, published prefecture and saved filters intersect without mutating input',()=>{
 const baseline=JSON.stringify(data),s=data.stations.find(s=>s.name==='吉祥寺'),state={...parse(''),q:'吉祥寺 中央',line:'pc_jr_chuo_rapid',pref:'13',favorites:true};
 assert.deepEqual(filterStations(data,students,state,[s.id]).map(x=>x.id),[s.id]);assert.equal(filterStations(data,students,state,[]).length,0);
 assert.equal(filterStations(data,students,{...state,pref:'11'},[s.id]).length,0);assert.equal(JSON.stringify(data),baseline);
});
test('observed zero remains visible; suppressed values are null and always sort last',()=>{
 const d=structuredClone(data),s=d.stations.find(s=>stationValue(d,students,s,'restaurants')!==null),mesh=d.meshContexts[s.meshCode],c=mesh.economicComponents[0];
 c.restaurants={value:0,status:'observed_zero',raw:'0'};assert.equal(stationValue(d,students,s,'restaurants'),0);
 c.restaurants={value:99999,status:'suppressed',raw:'X'};assert.equal(stationValue(d,students,s,'restaurants'),null);
 for(const dir of ['asc','desc']){const ss=filterStations(d,students,{...parse(''),dir});const i=ss.findIndex(s=>stationValue(d,students,s,'restaurants')===null);assert.ok(i>=0);assert.ok(ss.slice(i).every(s=>stationValue(d,students,s,'restaurants')===null));}
});
test('availability filtering cannot hide every station when sorting by name or station order',()=>{
 for(const sort of ['name','order']){const s={...parse(''),sort,available:true};assert.equal(filterStations(data,students,s).length,data.stations.length);}
 const s={...parse(''),available:true};assert.ok(filterStations(data,students,s).every(x=>stationValue(data,students,x,'restaurants')!==null));
});
test('line order preserves the 24 Chuo records and TX public endpoint',()=>{
 const s={...parse(''),sort:'order',line:'pc_jr_chuo_rapid'};assert.deepEqual(filterStations(data,students,s).map(x=>x.id),data.routes.find(r=>r.id===s.line).stationIds);
 s.line='pc_tsukuba_express';assert.equal(filterStations(data,students,s).at(-1).name,'柏たなか');
});
test('prefecture facets describe published components rather than claimed station municipality',()=>{
 const s=data.stations.find(s=>s.name==='町田');assert.deepEqual(stationPrefectures(data,s).sort(),['13','14']);assert.equal(stationValue(data,students,s,'restaurants'),null);assert.match(missingReason(data,students,s,'restaurants'),/複数都県/);
 const no=data.stations.find(s=>s.name==='みなみ寄居');assert.deepEqual(stationPrefectures(data,no),[]);
});
test('student residents remain 2020 observed people and same-area derived shares',()=>{
 const s=data.stations.find(s=>s.name==='東海大学前');assert.equal(stationValue(data,students,s,'university'),350);assert.equal(stationValue(data,students,s,'population'),1882);assert.equal(stationValue(data,students,s,'studentShare'),350/1882*100);
 const c=metricCoverage(data,students,s);assert.ok(c.count<=c.total);assert.equal(c.total,9);
 assert.match(METRIC_DETAILS.university.note,/住んでいる/);assert.match(METRIC_DETAILS.employees.note,/オフィス面積ではない/);
});

test('a direct line URL freezes one real line independently of the theme',()=>{const a=parse('#view=line'),b=parse('#view=line&theme=students');assert.equal(a.line,data.routes[0].id);assert.equal(b.line,a.line);});
