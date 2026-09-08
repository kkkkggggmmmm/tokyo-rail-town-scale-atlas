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
export function moneyLabel(observation){if(!observation)return '—';if(observation.status==='below_rounding_unit')return '単位未満';if(!Number.isFinite(observation.value))return observation.status==='suppressed'?'秘匿':'—';return new Intl.NumberFormat('ja-JP',{maximumFractionDigits:2}).format(observation.value/100);}
