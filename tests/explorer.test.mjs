import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import {parseState, visibleCases, routeCases, commonCases} from '../dist/app.mjs';
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
