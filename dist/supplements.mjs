// Source observations remain separate from canonical centers and CoreScale.
export function studentComponent(studentData,meshCode,prefectureCode){return studentData?.meshContexts?.[meshCode]?.components?.find(c=>c.prefectureCode===prefectureCode)||null;}
export function studentCount(studentData,station,key='university'){
 const components=studentData?.meshContexts?.[station.meshCode]?.components||[];
 if(components.length!==1)return null;
 const c=components[0];if(String(c.processingCode)!=='0'||(c.sourcePartitionCodes&&c.sourcePartitionCodes.length!==1))return null;
 const o=c[key];return o&&['observed','observed_zero'].includes(o.status)&&Number.isFinite(o.value)?o.value:null;
}
export function studentShare(data,studentData,station,prefectureCode){
 const mesh=data.meshContexts[station.meshCode];const cs=studentData?.meshContexts?.[station.meshCode]?.components||[];
 if(cs.length!==1||(mesh?.populationComponents||[]).length!==1)return null;
 const c=cs[0],p=mesh.populationComponents[0];
 if(prefectureCode&&c.prefectureCode!==prefectureCode)return null;
 if(c.referenceDate!==p.referenceDate)return null;
 if(c.prefectureCode!==p.prefectureCode||String(c.processingCode)!=='0'||String(p.processingCode)!=='0')return null;
 if(c.aggregationTarget||c.aggregatedSourceMeshCodes||p.aggregationTarget||p.aggregatedSourceMeshCodes)return null;
 if(c.sourcePartitionCodes?.length>1||p.sourcePartitionCodes?.length>1)return null;
 const n=c.university?.value,d=p.value;if(!['observed','observed_zero'].includes(c.university?.status)||!['observed','observed_zero'].includes(p.status)||!Number.isFinite(n)||!Number.isFinite(d)||d<=0||n<0||n>d)return null;
 return 100*n/d;
}
export function filterDistricts(districts,{query='',prefecture='all'}={}){const q=query.trim().normalize('NFKC');return districts.filter(d=>(prefecture==='all'||d.prefecture_code===prefecture)&&(!q||(d.name+' '+d.municipality_name).normalize('NFKC').includes(q)));}
export function districtTotal(district){const keys=['retail_sales_million_yen','food_service_sales_million_yen','personal_service_sales_million_yen'];const obs=keys.map(k=>district.metrics[k]);return obs.every(o=>o&&['observed','below_rounding_unit'].includes(o.status)&&Number.isFinite(o.value))?obs.reduce((s,o)=>s+o.value,0):null;}
export const DISTRICT_METRICS={
 retail_sales_million_yen:{label:'小売売上',unit:'億円／2020年'},
 food_service_sales_million_yen:{label:'飲食サービス売上',unit:'億円／2020年'},
 personal_service_sales_million_yen:{label:'生活関連サービス売上',unit:'億円／2020年'},
 total:{label:'3業種売上計',unit:'億円／2020年・公表値の和'},
 retail_sales_floor_sqm:{label:'小売売場面積',unit:'㎡／2021年'}
};
export function districtSortPatch(sort,dir,key){return Object.hasOwn(DISTRICT_METRICS,key)?{districtSort:key,districtDir:sort===key&&dir==='desc'?'asc':'desc'}:{districtSort:'source',districtDir:'desc'};}
export function rankDistricts(districts,{query='',prefecture='all',sort='source',dir='desc'}={}){
 const ranked=Object.hasOwn(DISTRICT_METRICS,sort);
 const rows=filterDistricts(districts,{query,prefecture}).map(district=>{
  const o=district.metrics[sort];
  const value=!ranked?null:sort==='total'?districtTotal(district):o&&['observed','observed_zero','below_rounding_unit'].includes(o.status)&&Number.isFinite(o.value)?o.value:null;
  return {district,value,rank:null};
 });
 if(ranked){
  rows.sort((a,b)=>a.value===null?(b.value===null?0:1):b.value===null?-1:(dir==='asc'?1:-1)*(a.value-b.value));
  let previous=null,rank=0;
  rows.forEach((r,i)=>{if(r.value!==null){if(r.value!==previous)rank=i+1;r.rank=rank;previous=r.value;}});
 }
 return {rows,ranked,eligible:rows.filter(r=>r.value!==null).length};
}
export function moneyLabel(observation){if(!observation)return '—';if(observation.status==='below_rounding_unit')return '単位未満';if(!Number.isFinite(observation.value))return observation.status==='suppressed'?'秘匿':'—';return new Intl.NumberFormat('ja-JP',{maximumFractionDigits:2}).format(observation.value/100);}
