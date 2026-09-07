import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import {parseState, visibleCases, routeCases, commonCases, summarizeCases, infographicBase, infographicCases} from '../dist/app.mjs';
const data = JSON.parse(readFileSync(new URL('../dist/data.json', import.meta.url)));

test('unknown URLs and repeated routes cannot expand public scope', () => {
  const state=parseState('#view=secret&line=N03&town=GE060&compare=bad,bad',data);
  assert.equal(state.view,'map');assert.equal(state.town,'');assert.equal(state.line,data.routes[0].id);
  assert.equal(state.compare.length,2);
});
test('station search works across the currently selected route and preserves empty results',()=>{
  const state=parseState('',data);
  assert.equal(visibleCases(data,{...state,q:'北朝霞'})[0].id,'GE037');
  assert.equal(visibleCases(data,{...state,q:'存在しない駅'}).length,0);
  assert.equal(visibleCases(data,{...state,line:'all'}).length,44);
});
test('profile order is reference order, never score order',()=>{
  assert.deepEqual(routeCases(data,data.routes[0].id).map(c=>c.id),['GE001','GE002','GE003','GE004','GE005','GE006','GE007']);
  assert.equal(routeCases(data,data.routes[7].id).length,4);
  assert.equal(routeCases(data,'unknown').length,0);
});
test('common cases are intersection and deduplicated, not a sum of memberships',()=>{
  assert.deepEqual(commonCases(data,[data.routes[0].id,data.routes[4].id]).map(c=>c.id),['GE002']);
  assert.deepEqual(commonCases(data,[data.routes[0].id,data.routes[3].id]),[]);
});
test('URL restores view, search, detail and up to four selected routes',()=>{
  const state=parseState('#view=profile&line='+data.routes[4].id+'&town=GE002&q=新宿&compare='+data.routes.map(r=>r.id).join(','),data);
  assert.equal(state.view,'profile');assert.equal(state.town,'GE002');assert.equal(state.q,'新宿');assert.equal(state.compare.length,4);
});

test('infographics count unique candidates and allow overlapping reference tags', () => {
  const summary = summarizeCases(data.cases);
  assert.equal(summary.total,44);
  assert.equal(summary.multipleStations,29);
  assert.deepEqual(Object.fromEntries(summary.prefectures.map(x=>[x.label,x.count])), {'東京都':23,'神奈川県':7,'埼玉県':7,'千葉県':7});
  assert.deepEqual(Object.fromEntries(summary.features.map(x=>[x.label,x.count])), {'買い物':16,'飲食・夜の街':22,'オフィス':10,'日々の暮らし':10,'観光・余暇':9,'商店街':8,'大型商業施設':4,'計画的な街づくり':1});
  assert.ok(summary.features.reduce((sum,x)=>sum+x.count,0) > summary.total);
  const routeMemberships = data.routes.flatMap(r=>routeCases(data,r.id));
  assert.equal(routeMemberships.length,50);
  assert.deepEqual(summarizeCases(routeMemberships),summary);
});

test('duplicate tags and repeated station names do not inflate counts', () => {
  const sample = {id:'test', features:['買い物','買い物'], prefectures:['東京都','東京都'], stations:['駅A','駅A']};
  const summary = summarizeCases([sample,sample]);
  assert.equal(summary.total,1);
  assert.equal(summary.features.find(x=>x.label==='買い物').count,1);
  assert.equal(summary.prefectures[0].count,1);
  assert.equal(summary.multipleStations,0);
  assert.deepEqual(summarizeCases([]).features.map(x=>x.count),Array(8).fill(0));
});

test('chart filters restore from URL and intersect without changing chart denominator', () => {
  const state = parseState('#view=insights&line=all&feature=買い物&prefecture=東京都&relation=multiple&town=GE002',data);
  assert.equal(state.view,'insights');assert.equal(state.town,'GE002');
  const expected = data.cases.filter(c=>c.features.includes('買い物') && c.prefectures.includes('東京都') && new Set(c.stations).size>1);
  assert.deepEqual(infographicCases(data,state),expected);
  assert.equal(summarizeCases(infographicBase(data,state)).total,44);
  assert.ok(expected.length>0 && expected.length<44);
  const impossible={...state,feature:'計画的な街づくり',prefecture:'神奈川県'};
  assert.deepEqual(infographicCases(data,impossible),[]);
});

test('route-specific chart denominators use only that reference route', () => {
  for(const route of data.routes){
    const state=parseState('#view=insights&line='+route.id,data);
    const base=infographicBase(data,state), summary=summarizeCases(base);
    assert.equal(summary.total,route.caseIds.length);
    assert.ok(summary.features.every(x=>x.count<=summary.total));
    assert.deepEqual(infographicCases(data,{...state,relation:'multiple'}).concat(infographicCases(data,{...state,relation:'single'})).map(c=>c.id).sort(),route.caseIds.toSorted());
  }
});

test('unknown filter values cannot introduce nonpublic tags, areas or candidates', () => {
  const state=parseState('#view=insights&line=all&feature=機密&prefecture=茨城県&relation=other&town=GE045',data);
  assert.equal(state.feature,'');assert.equal(state.prefecture,'');assert.equal(state.relation,'');assert.equal(state.town,'');
  assert.equal(infographicCases(data,state).length,44);
  assert.ok(infographicCases(data,state).every(c=>c.scale===null && c.scaleStatus==='not_estimated'));
});
