import assert from 'node:assert/strict';
import fs from 'node:fs';
import {test} from 'node:test';
import {mergeNetworkData,belongsToRoute,comparisonRoute,routeDestination,stationCaption} from '../dist/network-model.mjs';
import {parseExplorerState,serializeExplorerState,filterStations,stationValue} from '../dist/explorer-model.mjs';
import {benchmark,searchSuggestions,lineSlice,quantityFeatures} from '../dist/atlas-insights.mjs';
const read=f=>JSON.parse(fs.readFileSync(new URL('../dist/'+f+'.json',import.meta.url)));
const base=read('data'),network=read('network'),oldStudents=read('students');
const data=mergeNetworkData(base,network),students={...oldStudents,meshContexts:{...network.studentMeshContexts,...oldStudents.meshContexts}};
test('network merge keeps every existing station observation and all eight ordered corridors unchanged',()=>{
 assert.equal(data.stations.length,1592);assert.equal(new Set(data.stations.map(s=>s.groupId)).size,1271);
 assert.deepEqual(data.routes,base.routes);assert.equal(network.coverage.scopeStationRecords,1569);assert.equal(network.coverage.unresolvedStationRecords,0);
 for(const old of base.stations){const {networkRouteIds,...s}=data.stations.find(x=>x.id===old.id);assert.deepEqual(s,old);assert.ok(networkRouteIds.length);}
 for(const [m,c] of Object.entries(base.meshContexts))assert.deepEqual(data.meshContexts[m],c);
 for(const route of base.routes)assert.deepEqual(lineSlice(data,route.id).map(s=>s.id),route.stationIds);
});
test('all named reach anchors have real source-backed station and statistical records',()=>{
 for(const name of ['千葉','土気','大宮','浦和','東岩槻','藤沢','湘南台','片瀬江ノ島','高尾']){
  const ss=data.stations.filter(s=>s.name===name);assert.ok(ss.length,name);
  assert.ok(ss.some(s=>stationValue(data,students,s,'ridership')!==null),name);
  assert.ok(ss.some(s=>stationValue(data,students,s,'restaurants')!==null),name);
 }
 assert.equal(data.stations.some(s=>s.name==='守谷'),false);
 const f=data.stations.find(s=>s.name==='湘南台'&&s.operator==='小田急電鉄');assert.equal(stationValue(data,students,f,'university'),406);
});
test('formal route search opens a geographic filter and does not invent an ordered line',()=>{
 const r=data.officialRoutes.find(r=>r.name==='江ノ島線');assert.ok(r);assert.equal(r.orderStatus,'unconfirmed');
 const state={...parseExplorerState('',data),...routeDestination(data,r.id)};
 assert.equal(state.view,'map');assert.equal(parseExplorerState(serializeExplorerState(state),data).line,r.id);
 assert.deepEqual(new Set(filterStations(data,students,state).map(s=>s.id)),new Set(r.stationIds));
 assert.equal(parseExplorerState('#line='+r.id+'&sort=order',data).sort,'name');
 assert.ok(data.routes.some(x=>x.id===parseExplorerState('#view=line&line='+r.id,data).line));
 assert.equal(lineSlice(data,r.id).length,0);
 assert.ok(searchSuggestions(data,read('commercial-districts'),read('cafes'),'江ノ島線').some(s=>s.kind==='officialRoutes'&&s.id===r.id));
});
test('new stations compare against their selected formal route and show distinguishing route names',()=>{
 const s=data.stations.find(s=>s.name==='藤沢'&&s.operator==='小田急電鉄'),r=comparisonRoute(data,s,'all');
 assert.equal(r.name,'江ノ島線');assert.equal(belongsToRoute(s,r.id),true);assert.match(stationCaption(data,s),/小田急電鉄.*江ノ島線/);
 const b=benchmark(data,students,s,'restaurants',{scope:'line',line:r.id});assert.equal(b.label,r.name);assert.ok(b.total<data.stations.length);
});
test('last page is reachable beyond1000 records and URL state preserves the selection',()=>{
 const state={...parseExplorerState('#page=160',data),station:data.stations.at(-1).id};
 assert.equal(state.page,160);assert.deepEqual(parseExplorerState(serializeExplorerState(state),data),state);
 const rows=filterStations(data,students,state);assert.equal(rows.slice(1590,1600).length,2);
});
test('missing sources stay visible and numeric comparisons never turn duplicates or absent values into zero',()=>{
 const absent=data.stations.find(s=>s.name==='海芝浦');assert.ok(absent);assert.equal(stationValue(data,students,absent,'restaurants'),null);
 assert.ok(filterStations(data,students,parseExplorerState('#q=海芝浦',data)).some(s=>s.id===absent.id));
 assert.equal(filterStations(data,students,parseExplorerState('#q=海芝浦&metric=restaurants&available=1',data)).length,0);
 for(const s of data.stations)if(s.ridership.status!=='observed'&&s.ridership.status!=='observed_zero')assert.equal(stationValue(data,students,s,'ridership'),null);
 assert.equal(quantityFeatures(data,students,data.stations,'restaurants').features.length,1252);
 assert.equal(quantityFeatures(data,students,data.stations,'routeCount').features.length,1271);
});
test('unclassified statistical partitions are a visible filter and retain transport data',()=>{
 const state=parseExplorerState('#pref=unknown',data);assert.equal(state.pref,'unknown');
 const rows=filterStations(data,students,state);assert.deepEqual(rows.map(s=>s.name).sort(),['みなみ寄居','新整備場','海芝浦'].sort());
 assert.equal(rows.find(s=>s.name==='新整備場').ridership.value,4366);
 assert.equal(parseExplorerState(serializeExplorerState(state),data).pref,'unknown');
});
