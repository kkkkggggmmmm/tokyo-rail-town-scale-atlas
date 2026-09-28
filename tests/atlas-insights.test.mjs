import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import {benchmark,composition,fixedScale,quantityRadius,quantityFeatures,scopeOutline,lineSlice,lineInsights,searchSuggestions,parseCamera} from '../dist/atlas-insights.mjs';
import {parseExplorerState,serializeExplorerState,filterStations} from '../dist/explorer-model.mjs';
const load=name=>JSON.parse(readFileSync(new URL('../dist/'+name+'.json',import.meta.url)));
const data=load('data'),students=load('students'),districts=load('commercial-districts'),cafes=load('cafes');
test('camera and comparison basis survive URL round trip and invalid camera is rejected',()=>{
 const s={...parseExplorerState('',data),camera:[139.66,35.7,12.4],lineCamera:[139.42,35.8,10.5],profileCamera:[139.75,35.7,14.1],outline:true,mapMetric:'retail',benchmark:'line',from:2,to:8};
 assert.deepEqual(parseExplorerState(serializeExplorerState(s),data),s);
 for(const v of ['','1,2','999,35,10','139,95,10','139,35,100','x,35,10'])assert.equal(parseCamera(v),null);
 assert.deepEqual(parseCamera('139,35,10'),[139,35,10]);
});
test('numeric circles are area proportional, have a fixed global scale and deduplicate meshes',()=>{
 const scale=fixedScale(data,students,'restaurants');assert.equal(quantityRadius(400,scale)**2/quantityRadius(100,scale)**2,4);assert.equal(quantityRadius(null,scale),0);assert.equal(quantityRadius(0,scale),0);
 const all=quantityFeatures(data,students,data.stations,'restaurants');assert.equal(all.features.length,218);assert.equal(new Set(all.features.map(f=>f.properties.mesh)).size,218);
 const nulls=all.features.filter(f=>f.properties.missing);assert.equal(nulls.length,4);assert.ok(nulls.every(f=>f.properties.value===-1&&!f.properties.zero));
 assert.equal(quantityFeatures(data,students,data.stations,'ridership').features.length,0);assert.equal(fixedScale(data,students,'studentShare').max,100);
 assert.equal(quantityFeatures(data,students,data.stations,'routeCount').features.length,216);
});
test('scope outline is only the existing statistical grid frame, even on a prefectural boundary',()=>{
 const s=data.stations.find(s=>s.name==='町田'),f=scopeOutline(data,s).features[0],b=data.meshContexts[s.meshCode].bounds;
 assert.equal(f.properties.meaning,'statistical_grid_frame_only');assert.equal(f.properties.partitioned,true);
 assert.deepEqual(f.geometry.coordinates[0],[[b[0],b[1]],[b[2],b[1]],[b[2],b[3]],[b[0],b[3]],[b[0],b[1]]]);
 assert.equal(benchmark(data,students,s,'ridership').median,null);
});
test('benchmarks deduplicate repeated station meshes and report the actual denominator',()=>{
 const s=data.stations[0],b=benchmark(data,students,s,'restaurants');assert.equal(b.count,214);assert.equal(b.total,218);
 const d=structuredClone(data);d.stations.push(structuredClone(d.stations[0]));assert.deepEqual(benchmark(d,students,s,'restaurants'),b);
 const line=benchmark(data,students,s,'restaurants',{scope:'line',line:s.routeIds[0]});assert.ok(line.total<b.total);assert.ok(line.count<=line.total);
});
test('two-sector composition states its denominator and never counts apparel twice',()=>{
 const s=data.stations.find(s=>composition(data,students,s)?.total>0),c=composition(data,students,s);assert.equal(c.total,c.food+c.retail);assert.ok(Math.abs(c.foodShare+c.retailShare-100)<1e-10);
 const d=structuredClone(data);d.meshContexts[s.meshCode].economicComponents[0].apparel.value=99999;assert.deepEqual(composition(d,students,s),c);
 d.meshContexts[s.meshCode].economicComponents[0].restaurants={value:null,status:'suppressed'};assert.equal(composition(d,students,s),null);
});
test('every line retains registered order while selected ranges and summaries change together',()=>{
 for(const r of data.routes){const ss=lineSlice(data,r.id);assert.deepEqual(ss.map(s=>s.id),r.stationIds);const partial=lineInsights(data,students,r.id,{from:2,to:5});assert.deepEqual(partial.stations.map(s=>s.id),r.stationIds.slice(2,6));assert.equal(partial.meshCount,new Set(partial.stations.map(s=>s.meshCode)).size);assert.ok(partial.metrics.restaurants.peaks.length<=3);}
});
test('search candidates distinguish station, route, official district and municipality destinations',()=>{
 assert.ok(searchSuggestions(data,districts,cafes,'横浜').some(s=>s.kind==='stations'));
 assert.ok(searchSuggestions(data,districts,cafes,'中央').some(s=>s.kind==='routes'));
 assert.ok(searchSuggestions(data,districts,cafes,'銀座').some(s=>s.kind==='districts'));
 assert.ok(searchSuggestions(data,districts,cafes,'新宿区').some(s=>s.kind==='municipalities'));
 assert.deepEqual(searchSuggestions(data,districts,cafes,''),[]);
});
test('data-available filter follows the map indicator even when sort differs',()=>{
 const s={...parseExplorerState('',data),mapMetric:'studentShare',sort:'name',available:true};assert.equal(filterStations(data,students,s).length,217);
});
