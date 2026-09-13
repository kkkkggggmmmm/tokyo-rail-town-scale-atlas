import {allRoutes,belongsToRoute,comparisonRoute,stationCaption} from './network-model.mjs';
import {METRIC_DETAILS,stationValue,stationPrefectures} from './explorer-model.mjs';
export const MAP_METRICS=['restaurants','retail','apparel','employees','university','studentShare','population','routeCount'];
export const GROUP_NAMES={stations:'駅',routes:'沿線（駅順確定）',officialRoutes:'正式路線（掲載範囲内）',districts:'商業地区',municipalities:'自治体'};
const median=values=>{const a=values.filter(Number.isFinite).sort((a,b)=>a-b);return a.length?(a[Math.floor((a.length-1)/2)]+a[Math.floor(a.length/2)])/2:null};
export function parseCamera(raw){if(!raw)return null;const a=raw.split(',').map(Number);return a.length===3&&a.every(Number.isFinite)&&a[0]>=-180&&a[0]<=180&&a[1]>=-85&&a[1]<=85&&a[2]>=7&&a[2]<=17?a:null;}
export function uniqueSamples(stations,key){return [...new Map(stations.map(s=>[key==='routeCount'?s.groupId:s.meshCode,s])).values()];}
export function benchmark(data,students,station,key,{scope='all',line='all',stations}={}){
 if(key==='ridership')return {median:null,count:0,total:0,unit:'',reason:'事業者によって集計基準が異なるため比較基準を計算しません。'};
 const route=station?comparisonRoute(data,station,line):null;
 const pool=stations||((scope==='line'&&route)?data.stations.filter(s=>belongsToRoute(s,route.id)):data.stations),samples=uniqueSamples(pool,key),values=samples.map(s=>stationValue(data,students,s,key)).filter(Number.isFinite);
 return {median:median(values),count:values.length,total:samples.length,unit:key==='routeCount'?'駅群':'区画',label:scope==='line'&&route?route.name:'掲載対象全体'};
}
export function composition(data,students,station){const food=stationValue(data,students,station,'restaurants'),retail=stationValue(data,students,station,'retail');if(food===null||retail===null)return null;const total=food+retail;return {food,retail,total,foodShare:total>0?100*food/total:null,retailShare:total>0?100*retail/total:null};}
export function fixedScale(data,students,key){if(!MAP_METRICS.includes(key))return {max:0,key,ratio:false};return {key,max:key==='studentShare'?100:Math.max(1,...data.stations.map(s=>stationValue(data,students,s,key)).filter(Number.isFinite)),ratio:key==='studentShare'};}
export function quantityRadius(value,scale){return Number.isFinite(value)&&value>=0&&scale.max>0?32*Math.sqrt(value/scale.max):0;}
export function quantityFeatures(data,students,stations,key){if(!MAP_METRICS.includes(key))return {type:'FeatureCollection',features:[]};return {type:'FeatureCollection',features:uniqueSamples(stations,key).map(s=>{const v=stationValue(data,students,s,key),b=data.meshContexts[s.meshCode]?.bounds;return {type:'Feature',geometry:{type:'Point',coordinates:key==='routeCount'||!b?s.coordinates:[(b[0]+b[2])/2,(b[1]+b[3])/2]},properties:{id:s.id,mesh:s.meshCode,value:v??-1,missing:v===null,zero:v===0}};})};}
export function scopeOutline(data,station){const bounds=data.meshContexts[station?.meshCode]?.bounds;if(!bounds)return {type:'FeatureCollection',features:[]};const [w,s,e,n]=bounds;return {type:'FeatureCollection',features:[{type:'Feature',properties:{mesh:station.meshCode,meaning:'statistical_grid_frame_only',partitioned:stationPrefectures(data,station).length!==1},geometry:{type:'Polygon',coordinates:[[[w,s],[e,s],[e,n],[w,n],[w,s]]]}}]};}
export function lineSlice(data,lineId,from=0,to=null){const r=data.routes.find(r=>r.id===lineId);if(!r)return[];const byId=new Map(data.stations.map(s=>[s.id,s])),ss=r.stationIds.map(id=>byId.get(id)).filter(Boolean),a=Math.max(0,Math.min(ss.length-1,from)),b=to===null?ss.length-1:Math.max(a,Math.min(ss.length-1,to));return ss.slice(a,b+1);}
export function lineInsights(data,students,lineId,{from=0,to=null}={}){const stations=lineSlice(data,lineId,from,to),samples=uniqueSamples(stations,'restaurants');const metrics=Object.fromEntries(['restaurants','retail','employees','apparel','studentShare'].map(key=>{const valid=samples.map(s=>({station:s,value:stationValue(data,students,s,key)})).filter(x=>x.value!==null).sort((a,b)=>b.value-a.value);return [key,{median:median(valid.map(x=>x.value)),count:valid.length,total:samples.length,peaks:valid.slice(0,3)}]}));return {stations,meshCount:samples.length,metrics};}
export function searchSuggestions(data,districts,cafes,query){const q=query.trim().normalize('NFKC').toLocaleLowerCase('ja');if(!q)return[];const has=t=>t.normalize('NFKC').toLocaleLowerCase('ja').includes(q);return [
 ...data.stations.filter(s=>has(s.name)).slice(0,4).map(s=>({kind:'stations',id:s.id,label:s.name,detail:stationCaption(data,s)})),
 ...data.routes.filter(r=>has(r.name)||has(r.shortName||'')).slice(0,4).map(r=>({kind:'routes',id:r.id,label:r.name,detail:r.start+' — '+r.end})),
 ...(data.officialRoutes||[]).filter(r=>has(r.name)||has(r.operator)).slice(0,4).map(r=>({kind:'officialRoutes',id:r.id,label:r.name,detail:r.operator+'・掲載'+r.stationIds.length+'駅レコード'})),
 ...districts.districts.filter(d=>has(d.name)).slice(0,4).map(d=>({kind:'districts',id:d.name,label:d.name,detail:d.municipality_name+'・売上データ'})),
 ...[...new Map(cafes.observations.filter(c=>has(c.area_name)&&c.approved_for_display).map(c=>[c.area_code,c])).values()].slice(0,4).map(c=>({kind:'municipalities',id:c.area_name,label:c.area_name,detail:'自治体全体の喫茶店データ'}))
 ];}
