import {DISTRICT_AREAS} from './district-areas.mjs';
import {allRoutes,belongsToRoute} from './network-model.mjs';
import {studentCount,studentShare,DISTRICT_METRICS} from './supplements.mjs';
// Camera parser stays local to keep the core state module free of circular imports.
const camera=raw=>{if(!raw)return null;const a=raw.split(',').map(Number);return a.length===3&&a.every(Number.isFinite)&&a[0]>=-180&&a[0]<=180&&a[1]>=-85&&a[1]<=85&&a[2]>=7&&a[2]<=17?a:null;};

export const METRIC_DETAILS={
 restaurants:{label:'飲食店数',short:'飲食',unit:'店',year:'2021年',scope:'駅所在500m区画・都県公表分',source:'economic',note:'産業76の飲食店。宿泊・持ち帰り配達専門業を含まない。',kind:'公表値'},
 retail:{label:'小売事業所数',short:'小売',unit:'事業所',year:'2021年',scope:'駅所在500m区画・都県公表分',source:'economic',note:'小売業全体の事業所数。衣服・身の回り品店も含む。',kind:'公表値'},
 apparel:{label:'衣服・身の回り品店',short:'衣服店',unit:'店',year:'2021年',scope:'駅所在500m区画・都県公表分',source:'economic',note:'産業57。織物・衣服・靴・身の回り品を含む。',kind:'公表値'},
 employees:{label:'全産業の従業者数',short:'従業者',unit:'人',year:'2021年',scope:'駅所在500m区画・都県公表分',source:'economic',note:'全産業の事業所で働く人。オフィス面積ではない。',kind:'公表値'},
 university:{label:'大学・大学院在学者',short:'在住学生',unit:'人',year:'2020年',scope:'駅所在500m区画・都県公表分',source:'population',note:'この区画に住んでいる在学者。大学へ通ってくる人数ではない。',kind:'公表値'},
 studentShare:{label:'大学・大学院在学者の住民比',short:'学生の住民比',unit:'%',year:'2020年',scope:'同一区画・同一都県の総人口比',source:'population',note:'大学・大学院在学者の居住人数 ÷ 同じ区画の総人口 ×100。',kind:'算出値'},
 population:{label:'居住人口',short:'住民',unit:'人',year:'2020年',scope:'駅所在500m区画・都県公表分',source:'population',note:'通常処理の人口のみ。秘匿・合算対象を単一区画の値としない。',kind:'公表値'},
 routeCount:{label:'接続する原資料上の路線',short:'路線数',unit:'路線',year:'2025年末',scope:'N02の同名・近接駅群',source:'rail',note:'事業者・正式路線の組数。運転系統や直通先の数とは異なる。',kind:'公表情報から算出'},
 ridership:{label:'1日あたりの駅利用',short:'駅利用',unit:'人/日',year:'2024年度',scope:'原資料の事業者別集計範囲',source:'access',note:'乗車・乗降や乗換の扱いが事業者ごとに異なる。合計・順位付けはしない。',kind:'公表値',sortable:false},
};
export const THEMES={
 all:{label:'街の規模',icon:'▦',metric:'restaurants',columns:['restaurants','retail','employees','studentShare']},
 food:{label:'飲食',icon:'♧',metric:'restaurants',columns:['restaurants','retail','employees']},
 shopping:{label:'買い物',icon:'◇',metric:'apparel',columns:['retail','apparel','restaurants']},
 work:{label:'仕事',icon:'▣',metric:'employees',columns:['employees','restaurants','retail']},
 students:{label:'学生・教育',icon:'⌂',metric:'studentShare',columns:['university','studentShare','population']},
 access:{label:'交通',icon:'▥',metric:'routeCount',columns:['ridership','routeCount','restaurants']},
};
const observed=o=>o&&['observed','observed_zero'].includes(o.status)&&Number.isFinite(o.value);
export function stationValue(data,students,station,key){
 if(!station)return null;
 if(key==='ridership')return Number.isFinite(station.ridership?.value)?station.ridership.value:null;
 if(key==='routeCount')return Number.isFinite(station.officialRouteCount)?station.officialRouteCount:null;
 if(key==='university')return studentCount(students,station);
 if(key==='studentShare')return studentShare(data,students,station);
 const m=data.meshContexts[station.meshCode];
 if(key==='population'){
  const cs=m?.populationComponents||[];if(cs.length!==1)return null;const c=cs[0];
  return c.sourcePartitionCodes?.length===1&&String(c.processingCode)==='0'&&!c.aggregationTarget&&!c.aggregatedSourceMeshCodes&&observed(c)?c.value:null;
 }
 const cs=m?.economicComponents||[];if(cs.length!==1||cs[0].sourcePartitionCodes?.length!==1)return null;
 return observed(cs[0][key])?cs[0][key].value:null;
}
export function stationPrefectures(data,station){const m=data.meshContexts[station.meshCode];return [...new Set([...(m?.economicComponents||[]),...(m?.populationComponents||[])].flatMap(c=>c.sourcePartitionCodes||[c.prefectureCode]))];}
export function normalizePins(ids,data){const valid=new Set(data.stations.map(s=>s.id));return [...new Set(ids)].filter(id=>valid.has(id)).slice(0,4);}
export function parseExplorerState(hash,data){
 const p=new URLSearchParams(hash.replace(/^#/,'')),routes=data.routes.map(r=>r.id),ids=new Set(data.stations.map(s=>s.id));
 const theme=Object.hasOwn(THEMES,p.get('theme'))?p.get('theme'):'all';
 const validColumns=(p.get('cols')||'').split(',').filter(k=>Object.hasOwn(METRIC_DETAILS,k));
 let compare=[...new Set((p.get('compare')||routes.slice(0,2).join(',')).split(','))].filter(id=>routes.includes(id)).slice(0,4);if(compare.length<2)compare=routes.slice(0,2);
 const sort=p.get('sort'),validMetric=k=>Object.hasOwn(METRIC_DETAILS,k)&&k!=='ridership';
 const line=p.get('line'),knownLines=allRoutes(data).map(r=>r.id),ordered=routes.includes(line);
 const sortKey=sort==='order'&&!ordered?'name':sort==='name'||sort==='order'||validMetric(sort)?sort:theme==='all'?'name':THEMES[theme].metric;
 return {view:['map','profile','compare','line','numbers','sources'].includes(p.get('view'))?p.get('view'):'map',detail:['stations','districts','cafes','context'].includes(p.get('detail'))?p.get('detail'):'districts',line:p.get('view')==='line'?(ordered?line:routes[0]):knownLines.includes(line)?line:'all',station:ids.has(p.get('station'))?p.get('station'):'',q:(p.get('q')||'').slice(0,80),theme,pref:['11','12','13','14','unknown'].includes(p.get('pref'))?p.get('pref'):'all',sort:sortKey,dir:p.get('dir')==='asc'||(!p.has('dir')&&sortKey==='name')?'asc':'desc',columns:validColumns.length?[...new Set(validColumns)]:THEMES[theme].columns,panel:p.get('panel')==='list'?'list':'map',page:Math.max(1,Math.min(Math.max(1,Math.ceil(data.stations.length/10)),Number.parseInt(p.get('page'),10)||1)),available:p.get('available')==='1',favorites:p.get('favorites')==='1',pins:normalizePins((p.get('pins')||'').split(','),data),compareMode:p.get('mode')==='lines'?'lines':'stations',compare,mapMetric:validMetric(p.get('metric'))?p.get('metric'):'none',camera:camera(p.get('cam')),lineCamera:camera(p.get('lcam')),profileCamera:camera(p.get('pcam')),outline:p.get('outline')!=='0',benchmark:p.get('baseline')==='line'?'line':'all',from:Math.max(0,Number.parseInt(p.get('from'),10)||0),to:p.has('to')&&p.get('to')!==''?Math.max(0,Number.parseInt(p.get('to'),10)||0):null,regionQuery:(p.get('rq')||'').slice(0,80),regionPref:['11','12','13','14'].includes(p.get('rp'))?p.get('rp'):'all',districtSort:Object.hasOwn(DISTRICT_METRICS,p.get('dsort'))?p.get('dsort'):'source',districtDir:p.get('ddir')==='asc'?'asc':'desc',districtMode:p.get('dmode')==='source'?'source':'areas',districtArea:DISTRICT_AREAS.some(a=>a.id===p.get('area'))?p.get('area'):''};
}
export function serializeExplorerState(s){const p=new URLSearchParams({view:s.view,detail:s.detail,line:s.line,station:s.station,q:s.q,theme:s.theme,pref:s.pref,sort:s.sort,dir:s.dir,cols:s.columns.join(','),panel:s.panel,page:String(s.page),available:s.available?'1':'0',favorites:s.favorites?'1':'0',pins:s.pins.join(','),mode:s.compareMode,compare:s.compare.join(','),rq:s.regionQuery,rp:s.regionPref,dsort:s.districtSort||'source',ddir:s.districtDir||'desc',dmode:s.districtMode||'areas',area:s.districtArea||'',metric:s.mapMetric||'none',cam:(s.camera||[]).join(','),lcam:(s.lineCamera||[]).join(','),pcam:(s.profileCamera||[]).join(','),outline:s.outline===false?'0':'1',baseline:s.benchmark||'all',from:String(s.from||0),to:s.to===null||s.to===undefined?'':String(s.to)});return '#'+p.toString();}
export function filterStations(data,students,state,favorites=[]){
 const terms=state.q.trim().normalize('NFKC').toLocaleLowerCase('ja').split(/\s+/).filter(Boolean),saved=new Set(favorites);
 const rows=data.stations.filter(s=>{
  if(state.line!=='all'&&!belongsToRoute(s,state.line))return false;
  const prefs=stationPrefectures(data,s);
  if(state.pref==='unknown'?prefs.length>0:state.pref!=='all'&&!prefs.includes(state.pref))return false;
  if(state.favorites&&!saved.has(s.id))return false;
  const availabilityKey=state.mapMetric&&state.mapMetric!=='none'?state.mapMetric:state.sort;
  if(state.available&&Object.hasOwn(METRIC_DETAILS,availabilityKey)&&stationValue(data,students,s,availabilityKey)==null)return false;
  const text=[s.name,s.operator,...data.routes.filter(r=>s.routeIds.includes(r.id)).map(r=>r.name),...(s.officialRouteMemberships||[]).map(m=>m.route)].join(' ').normalize('NFKC').toLocaleLowerCase('ja');
  return terms.every(q=>text.includes(q));
 });
 const sign=state.dir==='asc'?1:-1;
 return rows.sort((a,b)=>{
  if(state.sort==='name')return sign*a.name.localeCompare(b.name,'ja')||a.id.localeCompare(b.id);
  if(state.sort==='order')return (a.routePositions[state.line]??999)-(b.routePositions[state.line]??999)||a.name.localeCompare(b.name,'ja');
  const x=stationValue(data,students,a,state.sort),y=stationValue(data,students,b,state.sort);
  if(x===null&&y===null)return a.name.localeCompare(b.name,'ja');if(x===null)return 1;if(y===null)return -1;
  return sign*(x-y)||a.name.localeCompare(b.name,'ja')||a.id.localeCompare(b.id);
 });
}
export function metricCoverage(data,students,station){const keys=['restaurants','retail','apparel','employees','population','university','studentShare','routeCount','ridership'];return {count:keys.filter(k=>stationValue(data,students,station,k)!==null).length,total:keys.length};}
export function missingReason(data,students,s,key){
 if(key==='ridership')return s.ridership?.status==='duplicate_on_other_record'?'他レコードとの重複対象。合算していません。':'駅利用人数が非公表・未取得です。';
 const m=data.meshContexts[s.meshCode];if(stationPrefectures(data,s).length>1)return '複数都県の公表成分があるため、一つの区画値へ合算していません。';
 const cs=key==='university'||key==='studentShare'?students.meshContexts[s.meshCode]?.components:key==='population'?m?.populationComponents:m?.economicComponents;
 if(!cs?.length)return 'この区画の公表データを取得できていません。';
 if(cs.some(c=>String(c.processingCode)==='1'))return '複数区画の合算先。単一区画の比較から除外しています。';
 if(cs.some(c=>String(c.processingCode)==='2'||c[key]?.status==='suppressed'))return '原資料で秘匿されています。';
 return key==='studentShare'?'同じ範囲の在学者数と総人口を確認できないため算定していません。':'秘匿・未公表などで比較できる数値がありません。';
}
