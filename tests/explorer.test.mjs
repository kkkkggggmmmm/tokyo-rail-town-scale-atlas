import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import {parseState,routeStations,searchedStations,stationMetric,routeSummary,evaluateRoutes,median,formatValue,routeCsv,mapStyle,escapeHtml} from '../dist/app.mjs';
const data=JSON.parse(readFileSync(new URL('../dist/data.json',import.meta.url)));
test('URL state restricts scope and preserves known station, search and four routes',()=>{
 const bad=parseState('#view=bad&line=N03&station=GE060&compare=bad,bad',data);assert.equal(bad.view,'map');assert.equal(bad.station,'');assert.equal(bad.compare.length,2);
 const good=parseState('#view=numbers&station='+data.stations[0].id+'&compare='+data.routes.map(r=>r.id).join(','),data);assert.equal(good.station,data.stations[0].id);assert.equal(good.compare.length,4);
});
test('geographic pilot includes 24 Chuo stations and TX ends at 柏たなか',()=>{
 const chuo=routeStations(data,'pc_jr_chuo_rapid');assert.equal(chuo.length,24);assert.equal(chuo[0].name,'東京');assert.equal(chuo.at(-1).name,'高尾');assert.equal(routeStations(data,'pc_tsukuba_express').at(-1).name,'柏たなか');
 const state=parseState('',data);assert.ok(searchedStations(data,{...state,q:'横浜'}).some(s=>s.name==='横浜'));assert.equal(searchedStations(data,{...state,q:'存在しない駅'}).length,0);
});
test('null and suppressed values cannot become zero or ranks',()=>{
 assert.equal(formatValue(null),'—');assert.equal(formatValue(0),'0');assert.equal(median([null,undefined,0,10]),5);assert.equal(median([null]),null);
 const d=structuredClone(data),s=d.stations[0],c=d.meshContexts[s.meshCode].economicComponents[0];c.restaurants={value:null,status:'suppressed',raw:'X'};assert.equal(stationMetric(d,s,'restaurants'),null);
});
test('cross-prefecture components are not picked or added, including buffer-only components',()=>{
 const d=structuredClone(data),s=d.stations[0],mesh=d.meshContexts[s.meshCode];mesh.economicComponents=[{prefectureCode:'13',sourcePartitionCodes:['13','14'],restaurants:{value:10}},{prefectureCode:'14',sourcePartitionCodes:['13','14'],restaurants:{value:20}}];assert.equal(stationMetric(d,s,'restaurants'),null);
 mesh.economicComponents=[{prefectureCode:'13',sourcePartitionCodes:['13','19'],restaurants:{value:10}}];assert.equal(stationMetric(d,s,'restaurants'),null);
});
test('same mesh through multiple stations counts once per line',()=>{
 const d=structuredClone(data),route=d.routes[0],stations=routeStations(d,route.id);stations[1].meshCode=stations[0].meshCode;const summary=routeSummary(d,route.id);assert.equal(summary.stationCount,24);assert.equal(summary.meshCount,23);
});
test('S12 changes cannot influence commercial comparison',()=>{
 const base=evaluateRoutes(data).map(r=>({meanRank:r.meanRank,ranks:r.ranks,metrics:r.metrics}));const d=structuredClone(data);d.stations.forEach(s=>s.ridership.value=999999999);assert.deepEqual(evaluateRoutes(d).map(r=>({meanRank:r.meanRank,ranks:r.ranks,metrics:r.metrics})),base);
});
test('average-rank equation is explicit and coverage under 90 percent withholds it',()=>{
 for(const row of evaluateRoutes(data)){assert.equal(row.meanRank,Object.values(row.ranks).reduce((a,b)=>a+b,0)/3);}
 const d=structuredClone(data);for(const s of routeStations(d,d.routes[0].id).slice(0,4)){d.meshContexts[s.meshCode].economicComponents[0].restaurants.value=null;}
 assert.equal(evaluateRoutes(d)[0].meanRank,null);
});
test('transport CSV does not sum operators or replace missing counts',()=>{
 const csv=routeCsv(data,'pc_tokyo_metro_ginza');assert.ok(csv.includes('2024'));assert.ok(csv.includes('2021-06-01'));assert.ok(csv.includes('人/日・事業者別基準'));assert.ok(csv.startsWith('\uFEFF'));assert.equal(escapeHtml('<img>'),'&lt;img&gt;');
});
test('map uses real vector municipalities and rails, no schematic or road/POI layers',()=>{
 const style=mapStyle();assert.equal(style.version,8);assert.ok(style.sources.gsi.url.startsWith('pmtiles://https://cyberjapandata.gsi.go.jp/'));
 const layers=new Set(style.layers.map(l=>l['source-layer']).filter(Boolean));assert.deepEqual(layers,new Set(['AdmArea','WA','Cstline','AdmBdry','RailCL','Anno']));
 assert.ok(style.layers.some(l=>l.id==='municipality-names'));assert.ok(style.layers.some(l=>l.id==='station-names'));assert.ok(!JSON.stringify(style).includes('N03'));
});
