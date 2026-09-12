import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {boardRows,metricTile,themeBoard} from '../dist/theme-view.mjs';
import {parseExplorerState,stationValue} from '../dist/explorer-model.mjs';
const read=name=>JSON.parse(readFileSync(new URL('../dist/'+name+'.json',import.meta.url)));
const data=read('data'),students=read('students'),context=read('context');
const state=parseExplorerState('',data);

test('a selected operator station survives shared-mesh comparison deduplication',()=>{
 const s=data.stations.find(s=>s.id==='sta_03430551b0a042728f118418900fe7be');
 assert.ok(s);
 const result=boardRows(data,data.stations,{...state,station:s.id});
 assert.equal(result.rows[0].id,s.id);
 assert.equal(new Set(result.rows.map(s=>s.meshCode)).size,result.rows.length);
 const pins=data.stations.filter(x=>x.meshCode===s.meshCode).slice(0,2).map(s=>s.id);
 assert.deepEqual(boardRows(data,data.stations,{...state,pins}).rows.map(s=>s.id),pins);
});
test('theme tiles retain observed zero, withhold unavailable values, and show source years',()=>{
 const missing=data.stations.find(s=>stationValue(data,students,s,'restaurants')===null);
 assert.ok(missing);
 const html=metricTile(data,students,missing,'restaurants',state);
 assert.match(html,/<strong>—<\/strong>/);
 assert.match(html,/2021年/);
 const zero=data.stations.find(s=>stationValue(data,students,s,'apparel')===0);
 assert.ok(zero);
 assert.match(metricTile(data,students,zero,'apparel',state),/<strong>0<small>店<\/small>/);
});
test('student dashboard preserves residence scope and actual school access, not invented inflows',()=>{
 const s=data.stations.find(s=>s.name==='吉祥寺');
 const html=themeBoard(data,students,context,[s],{...state,station:s.id,theme:'students',columns:['university','studentShare']});
 assert.match(html,/住んでいる大学・大学院生/);
 assert.match(html,/2020年・駅所在500m区画/);
 assert.match(html,/data-state">未取得/);
 assert.match(html,/日能研 吉祥寺校/);
 assert.match(html,/徒歩1分（公式案内）/);
 assert.match(html,/表示項目を選んだ比較表/);
 assert.doesNotMatch(html,/24,310|36,400|個店率68/);
});
