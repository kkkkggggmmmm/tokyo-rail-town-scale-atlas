// Fixed collections of Table 2 leaf districts, not canonical center geometry.
// Selected-district sums authorized by DEC-0016; whole-town coverage remains unverified.
import {DISTRICT_METRICS} from './supplements.mjs';
export const AREA_SUM_METHOD = {version:'selected-district-sum-v1',sourceId:'estat2021_ricchi_table2',referenceSalesYear:2020,referenceFloorDate:'2021-06-01',geographicCoverage:'not_certified'};
export const DISTRICT_AREAS = [
  {
    "id": "browse_7db4ffb01f3e4732b1ec584839d0ad57",
    "name": "新宿",
    "sourceDistrictIds": [
      "13104019",
      "13104028",
      "13104029",
      "13104030",
      "13104036",
      "13104037",
      "13104039",
      "13104041",
      "13104042",
      "13104043",
      "13104045",
      "13113047",
      "13113048"
    ],
    "scopeNote": "東西口・歌舞伎町・新宿1〜4丁目・西新宿7丁目・南口側の13公表地区を合計。渋谷区側の南新宿商店会とタカシマヤタイムズスクエアを含み、新大久保は含みません。",
    "status": "table_defined_selection",
    "aggregationAllowed": false,
    "selectedDistrictSumAllowed": true
  },
  {
    "id": "browse_8517269ad97548e99ab4d953fcf861f8",
    "name": "銀座",
    "sourceDistrictIds": [
      "13102013",
      "13199002",
      "13199003"
    ],
    "scopeNote": "銀座地域と、原表で境界未定地域に記載された銀座インズ・銀座ファイブ・西銀座、銀座ナインの3公表地区を合計。有楽町・日比谷の別地区は含みません。",
    "status": "table_defined_selection",
    "aggregationAllowed": false,
    "selectedDistrictSumAllowed": true
  },
  {
    "id": "browse_c4aff408026b47d696589e7236ba5116",
    "name": "池袋",
    "sourceDistrictIds": [
      "13116009",
      "13116010",
      "13116011",
      "13116012",
      "13116022",
      "13116024",
      "13116025"
    ],
    "scopeNote": "東西口・地下街・サンシャイン・東池袋4・5丁目・西北部地域の7公表地区を合計。原表で別地区の目白・大塚は含みません。",
    "status": "table_defined_selection",
    "aggregationAllowed": false,
    "selectedDistrictSumAllowed": true
  },
  {
    "id": "browse_2d82001a8aae48b1a96586cfd70dde03",
    "name": "渋谷",
    "sourceDistrictIds": [
      "13113017",
      "13113018",
      "13113019",
      "13113020",
      "13113026",
      "13113039",
      "13113040",
      "13113044",
      "13113045",
      "13113046"
    ],
    "scopeNote": "駅東部・公園通り・道玄坂・奥渋など、以下の10公表地区を合計。原宿・表参道は別エリアです。",
    "status": "table_defined_selection",
    "aggregationAllowed": false,
    "selectedDistrictSumAllowed": true
  },
  {
    "id": "browse_cc8c1418bd27446a9e54698e0a40797c",
    "name": "日本橋",
    "sourceDistrictIds": [
      "13102001",
      "13102006"
    ],
    "scopeNote": "室町地域と日本橋地域の2公表地区を合計。人形町・京橋などの別地区は含みません。",
    "status": "table_defined_selection",
    "aggregationAllowed": false,
    "selectedDistrictSumAllowed": true
  },
  {
    "id": "browse_5b0240089a7c4ec4a5052ea60975b7f4",
    "name": "原宿・表参道",
    "sourceDistrictIds": [
      "13113015",
      "13113016",
      "13113025",
      "13103001"
    ],
    "scopeNote": "原宿駅周辺・神宮前2・3丁目周辺・原宿2丁目商店会と、港区の青山通り表参道周辺の4公表地区を合計。",
    "status": "table_defined_selection",
    "aggregationAllowed": false,
    "selectedDistrictSumAllowed": true
  },
  {
    "id": "browse_1228ae93dd6b45baac3b3a5a835cfd75",
    "name": "六本木",
    "sourceDistrictIds": [
      "13103007",
      "13103029",
      "13103031"
    ],
    "scopeNote": "六本木、六本木ヒルズ、東京ミッドタウンの3公表地区を合計。麻布十番・赤坂の別地区は含みません。",
    "status": "table_defined_selection",
    "aggregationAllowed": false,
    "selectedDistrictSumAllowed": true
  },
  {
    "id": "browse_b1613de41de74eab8f3b2d759d401809",
    "name": "吉祥寺",
    "sourceDistrictIds": [
      "13203001",
      "13203002"
    ],
    "scopeNote": "吉祥寺駅北口・南口の2公表地区を合計。商業集積地区として掲載されていない周辺の店舗は含みません。",
    "status": "table_defined_selection",
    "aggregationAllowed": false,
    "selectedDistrictSumAllowed": true
  }
];
export function areaDistricts(asset,area){const ids=new Set(area.sourceDistrictIds);return asset.districts.filter(d=>ids.has(d.source_district_id));}
export function filterAreas(asset,{query='',prefecture='all',areas=DISTRICT_AREAS}={}){
 const q=query.trim().normalize('NFKC');
 return areas.filter(area=>{const rows=areaDistricts(asset,area);return (prefecture==='all'||rows.some(d=>d.prefecture_code===prefecture))&&(!q||(area.name+' '+rows.map(d=>d.name+' '+d.municipality_name).join(' ')).normalize('NFKC').includes(q));});
}

const SALES_KEYS=['retail_sales_million_yen','food_service_sales_million_yen','personal_service_sales_million_yen'];
const usable=o=>o&&['observed','observed_zero','below_rounding_unit'].includes(o.status)&&Number.isFinite(o.value)&&o.value>=0;
export const areaSortKey=sort=>Object.hasOwn(DISTRICT_METRICS,sort)?sort:'retail_sales_million_yen';

export function aggregateArea(asset,area){
 const ids=area.sourceDistrictIds,records=new Map();
 for(const d of asset.districts){if(!records.has(d.source_district_id))records.set(d.source_district_id,[]);records.get(d.source_district_id).push(d);}
 const identityValid=area.selectedDistrictSumAllowed===true&&ids.length>0&&new Set(ids).size===ids.length&&ids.every(id=>records.get(id)?.length===1);
 const districts=areaDistricts(asset,area),metrics={};
 for(const key of Object.keys(DISTRICT_METRICS)){
  const keys=key==='total'?SALES_KEYS:[key],missing=[];let sum=0,observed=0,rounded=false;
  for(const id of ids)for(const metric of keys){
   const entries=records.get(id)||[],d=entries[0],o=d?.metrics?.[metric];
   if(entries.length===1&&usable(o)){sum+=o.value;observed++;rounded ||= o.status==='below_rounding_unit';}
   else missing.push({districtId:id,name:d?.name||id,metric,status:entries.length!==1?(entries.length?'duplicate_source_id':'source_row_missing'):o?.status||'not_acquired'});
  }
  const expected=ids.length*keys.length,complete=identityValid&&observed===expected;
  metrics[key]={value:complete?sum:null,complete,observed,expected,missing,rounded};
 }
 return {area,districts,metrics,identityValid};
}

export function rankAreas(asset,{query='',prefecture='all',sort='retail_sales_million_yen',dir='desc',areas=DISTRICT_AREAS}={}){
 sort=areaSortKey(sort);
 // Check the full registry before filtering: narrowing a search cannot hide a conflict.
 const owners=new Map();for(const a of areas)for(const id of new Set(a.sourceDistrictIds))owners.set(id,(owners.get(id)||0)+1);
 const rows=filterAreas(asset,{query,prefecture,areas}).map(area=>{
  const result=aggregateArea(asset,area);
  if(area.sourceDistrictIds.some(id=>owners.get(id)>1)){
   result.identityValid=false;
   for(const m of Object.values(result.metrics)){m.value=null;m.complete=false;}
  }
  return {...result,value:result.metrics[sort].value,rank:null};
 });
 rows.sort((a,b)=>a.value===null?(b.value===null?0:1):b.value===null?-1:(dir==='asc'?1:-1)*(a.value-b.value));
 let previous=null,rank=0;rows.forEach((r,i)=>{if(r.value!==null){if(r.value!==previous)rank=i+1;r.rank=rank;previous=r.value;}});
 return {rows,eligible:rows.filter(r=>r.value!==null).length,sort};
}
