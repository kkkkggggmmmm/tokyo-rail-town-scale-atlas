// Fixed collections of Table 2 leaf districts, not canonical center geometry.
// Selected-district sums authorized by DEC-0016/0017; whole-town coverage remains unverified.
import {DISTRICT_METRICS} from './supplements.mjs';
export const AREA_SUM_METHOD = {version:'selected-district-sum-v2',sourceId:'estat2021_ricchi_table2',referenceSalesYear:2020,referenceFloorDate:'2021-06-01',geographicCoverage:'not_certified'};
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
  },
  {
    "id": "browse_212f715b862b47d5b6a495c032030828",
    "name": "上野・御徒町",
    "sourceDistrictIds": [
      "13106002",
      "13106003",
      "13106004",
      "13106021",
      "13106022",
      "13106023",
      "13106024",
      "13106028",
      "13106029"
    ],
    "scopeNote": "上野駅周辺・上野2/4/6/7丁目、御徒町東西部、2K540、池之端の9公表地区を合計。谷中・鶯谷・浅草橋は含みません。",
    "status": "table_defined_selection",
    "aggregationAllowed": false,
    "selectedDistrictSumAllowed": true
  },
  {
    "id": "browse_c50f6958f70545f59ce4c6fa8b4a99f7",
    "name": "浅草",
    "sourceDistrictIds": [
      "13106007",
      "13106012",
      "13106013",
      "13106014",
      "13106015",
      "13106026",
      "13106027"
    ],
    "scopeNote": "浅草・雷門、花川戸、ひさご通り、千束通り、かっぱ橋本通り東部、寿2丁目、浅草西参道の7公表地区を合計。かっぱ橋道具街・本通り西部、入谷・竜泉、浅草橋は含みません。",
    "status": "table_defined_selection",
    "aggregationAllowed": false,
    "selectedDistrictSumAllowed": true
  },
  {
    "id": "browse_c7741dd53cb946b39a8f0f7368318de5",
    "name": "中野",
    "sourceDistrictIds": [
      "13114007",
      "13114017",
      "13114018"
    ],
    "scopeNote": "中野駅北口・南口と新井1丁目地域の3公表地区を合計。東中野・中野坂上・新井薬師は含みません。",
    "status": "table_defined_selection",
    "aggregationAllowed": false,
    "selectedDistrictSumAllowed": true
  },
  {
    "id": "browse_e75d031ac0024e59ae43fbcee02cd060",
    "name": "高円寺",
    "sourceDistrictIds": [
      "13115011",
      "13115012",
      "13115014",
      "13115031",
      "13115036"
    ],
    "scopeNote": "高円寺駅南北口、高円寺南2・3丁目、北2・3丁目、新高円寺駅周辺の5公表地区を合計。東高円寺・阿佐ケ谷は含みません。",
    "status": "table_defined_selection",
    "aggregationAllowed": false,
    "selectedDistrictSumAllowed": true
  },
  {
    "id": "browse_27df785f43894c1aa5779a8e7073e5ff",
    "name": "荻窪",
    "sourceDistrictIds": [
      "13115007",
      "13115008",
      "13115009",
      "13115033"
    ],
    "scopeNote": "荻窪駅南北口・北口大通り商店街・川端通り商店街の4公表地区を合計。西荻窪、荻窪1・2丁目や八丁通りなど別地区は含みません。",
    "status": "table_defined_selection",
    "aggregationAllowed": false,
    "selectedDistrictSumAllowed": true
  },
  {
    "id": "browse_86c791a9bbc741f28ba718f5a8fb0a60",
    "name": "立川",
    "sourceDistrictIds": [
      "13202001",
      "13202003"
    ],
    "scopeNote": "立川駅北口・南口の2公表地区を合計。高松町・羽衣町・若葉町など別地区は含みません。",
    "status": "table_defined_selection",
    "aggregationAllowed": false,
    "selectedDistrictSumAllowed": true
  },
  {
    "id": "browse_69faf321d21e4db8b127b96e1d14cb75",
    "name": "八王子",
    "sourceDistrictIds": [
      "13201001",
      "13201002",
      "13201003",
      "13201004",
      "13201005",
      "13201022",
      "13201025",
      "13201032",
      "13201034",
      "13201035",
      "13201038",
      "13201047"
    ],
    "scopeNote": "八王子駅南北口・京王八王子駅周辺に横山町・八幡町・八日町・本町・大横町などを加えた12公表地区を合計。西八王子・高尾・南大沢など別拠点は含みません。",
    "status": "table_defined_selection",
    "aggregationAllowed": false,
    "selectedDistrictSumAllowed": true
  },
  {
    "id": "browse_1651275fbee8438bb87cff4c1e51a9ce",
    "name": "町田",
    "sourceDistrictIds": [
      "13209005",
      "13209017",
      "13209018",
      "13209019",
      "13209020",
      "13209021",
      "13209023",
      "13209025"
    ],
    "scopeNote": "原町田1〜6丁目、森野1・2丁目、中町1・3丁目の8公表地区を合計。成瀬・鶴川・南町田や相模原市側の地区は含みません。",
    "status": "table_defined_selection",
    "aggregationAllowed": false,
    "selectedDistrictSumAllowed": true
  },
  {
    "id": "browse_1128f261c4194a30b60c85ee214ed9df",
    "name": "横浜駅周辺",
    "sourceDistrictIds": [
      "14102012",
      "14102019",
      "14103004",
      "14103005",
      "14103007",
      "14103008",
      "14103009",
      "14103011",
      "14103012",
      "14103013",
      "14103017",
      "14103018",
      "14103024",
      "14103025"
    ],
    "scopeNote": "東西口、台町・鶴屋町、岡野・平沼、駅前商業施設の14公表地区を合計。みなとみらい・関内・元町は含みません。原表の西口地区はシャルを除外しますが、シャル単独の行はこの集計にありません。",
    "status": "table_defined_selection",
    "aggregationAllowed": false,
    "selectedDistrictSumAllowed": true
  },
  {
    "id": "browse_7ff3e8ad96c5482d8045434140e2d3a8",
    "name": "みなとみらい・桜木町",
    "sourceDistrictIds": [
      "14103016",
      "14103019",
      "14103020",
      "14103023",
      "14104022",
      "14104042",
      "14104047",
      "14104048"
    ],
    "scopeNote": "みなとみらいの公表地区と桜木町駅の掲載商業施設、計8地区を合計。野毛・日ノ出町・関内の別地区は含みません。",
    "status": "table_defined_selection",
    "aggregationAllowed": false,
    "selectedDistrictSumAllowed": true
  },
  {
    "id": "browse_b0e9c48a9339415c87fbfe366dd719f6",
    "name": "川崎駅周辺",
    "sourceDistrictIds": [
      "14131001",
      "14131002",
      "14131003",
      "14131004",
      "14131005",
      "14131006",
      "14131007",
      "14131008",
      "14131024",
      "14132001",
      "14132016"
    ],
    "scopeNote": "川崎駅東側9地区と、幸区側の中幸町・南幸町、ラゾーナの11公表地区を合計。川崎大師・八丁畷・鹿島田の別地区は含みません。",
    "status": "table_defined_selection",
    "aggregationAllowed": false,
    "selectedDistrictSumAllowed": true
  },
  {
    "id": "browse_52055a89f56d49f98e5b93cc7948284c",
    "name": "大宮",
    "sourceDistrictIds": [
      "11103008",
      "11103011",
      "11103015",
      "11103019",
      "11103079",
      "11103080",
      "11103085",
      "11103086",
      "11103087",
      "11103091",
      "11103096",
      "11103097",
      "11103099",
      "11103100"
    ],
    "scopeNote": "大宮駅東西の商店街・駅ビルなど、下記14公表地区を合計。大成三丁目商工会とコクーン新都心は含みません。値が秘匿・該当数字なしの地区も対象に残しています。",
    "status": "table_defined_selection",
    "aggregationAllowed": false,
    "selectedDistrictSumAllowed": true
  },
  {
    "id": "browse_cb1bc0329195460fa3b1008717f99c2d",
    "name": "浦和",
    "sourceDistrictIds": [
      "11107002",
      "11107006",
      "11107010",
      "11107016",
      "11107020",
      "11107023",
      "11107025",
      "11107060",
      "11107061",
      "11107063"
    ],
    "scopeNote": "浦和駅周辺の商店街・コルソ・パルコなど10公表地区を合計。北浦和・与野は含みません。平和通り商店街（11107031）は所属確認が未了のため対象外で、街全域の網羅は未確認です。",
    "status": "table_defined_selection",
    "aggregationAllowed": false,
    "selectedDistrictSumAllowed": true
  },
  {
    "id": "browse_05942e0370014743bd5abcd0c52d3a15",
    "name": "川越・本川越",
    "sourceDistrictIds": [
      "11201001",
      "11201003",
      "11201004",
      "11201005",
      "11201007",
      "11201010",
      "11201011",
      "11201014",
      "11201015",
      "11201019",
      "11201023",
      "11201037",
      "11201038",
      "11201039",
      "11201041",
      "11201042",
      "11201045"
    ],
    "scopeNote": "川越市の公表地区から指定した17地区を合計。一番街・菓子屋横丁、川越駅東西口、本川越ステーションビルなどを含みます。六栄会・川越名店街を含む各地区の位置・境界は未確認で、街全域の網羅は保証しません。霞ケ関・新河岸・南台の別地区は含みません。",
    "status": "table_defined_selection",
    "aggregationAllowed": false,
    "selectedDistrictSumAllowed": true
  },
  {
    "id": "browse_7e82df969aa24164a996e1a623e4e633",
    "name": "千葉駅周辺",
    "sourceDistrictIds": [
      "12101019",
      "12101020",
      "12101021",
      "12101022",
      "12101026",
      "12101030"
    ],
    "scopeNote": "千葉駅の駅ビル・富士見町・栄町・千葉公園通りなど6公表地区を合計。西千葉・本千葉と蘇我の別地区は含みません。",
    "status": "table_defined_selection",
    "aggregationAllowed": false,
    "selectedDistrictSumAllowed": true
  },
  {
    "id": "browse_b3753fa97bea4dc1be8332256093a1d9",
    "name": "船橋駅周辺",
    "sourceDistrictIds": [
      "12204002",
      "12204003",
      "12204005",
      "12204006",
      "12204007",
      "12204008",
      "12204009",
      "12204047",
      "12204054",
      "12204078",
      "12204079"
    ],
    "scopeNote": "船橋駅南北の商店街・駅ビル・百貨店など11公表地区を合計。西船橋・南船橋・津田沼の別地区は含みません。御殿通りの秘匿値も欠損として残しています。",
    "status": "table_defined_selection",
    "aggregationAllowed": false,
    "selectedDistrictSumAllowed": true
  },
  {
    "id": "browse_b10157925bd143de870b6bc677f91528",
    "name": "柏",
    "sourceDistrictIds": [
      "12217001",
      "12217017",
      "12217018"
    ],
    "scopeNote": "柏駅東西口と高島屋ステーションモールの3公表地区を合計。柏の葉・南柏・大山台・アリオ柏の別地区は含みません。",
    "status": "table_defined_selection",
    "aggregationAllowed": false,
    "selectedDistrictSumAllowed": true
  },
  {
    "id": "browse_62a2b78030274707ab52326e62cbc014",
    "name": "松戸駅周辺",
    "sourceDistrictIds": [
      "12207007",
      "12207008",
      "12207012",
      "12207091",
      "12207092",
      "12207096",
      "12207097",
      "12207098",
      "12207099",
      "12207100",
      "12207103",
      "12207104"
    ],
    "scopeNote": "松戸駅東西の掲載商店会から指定した12公表地区を合計。北松戸・新松戸・馬橋・小金・五香・八柱は含みません。みやまえ会・春雨会・わかば商店会などは帰属未確認で対象外です。",
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
