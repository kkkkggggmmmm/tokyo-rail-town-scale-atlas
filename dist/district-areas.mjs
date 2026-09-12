// Editorial navigation associations, not canonical center membership or approved aggregation.
// Source: existing estat2021_ricchi_table2 district IDs; no inferred polygon.
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
    "scopeNote": "東西口・歌舞伎町・南口側の関連地区。渋谷区側の地区も確認対象。新大久保などとの境界は未確定。",
    "status": "boundary_and_membership_unverified",
    "aggregationAllowed": false
  },
  {
    "id": "browse_8517269ad97548e99ab4d953fcf861f8",
    "name": "銀座",
    "sourceDistrictIds": [
      "13102013",
      "13199002",
      "13199003"
    ],
    "scopeNote": "銀座地域のほか、境界未定地域に記載された銀座の施設を確認対象に含める。有楽町・日比谷との境界は未確定。",
    "status": "boundary_and_membership_unverified",
    "aggregationAllowed": false
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
    "scopeNote": "東西口・地下街・サンシャインなどの関連地区。東池袋のどこまでを一体の街とするかは未確定。",
    "status": "boundary_and_membership_unverified",
    "aggregationAllowed": false
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
    "scopeNote": "駅東部・公園通り・道玄坂などの関連地区。奥渋・青山側の境界と地区同士の範囲は未確定。",
    "status": "boundary_and_membership_unverified",
    "aggregationAllowed": false
  },
  {
    "id": "browse_cc8c1418bd27446a9e54698e0a40797c",
    "name": "日本橋",
    "sourceDistrictIds": [
      "13102001",
      "13102006"
    ],
    "scopeNote": "室町地域と日本橋地域を確認対象にする。人形町・京橋など周辺地域との境界は未確定。",
    "status": "boundary_and_membership_unverified",
    "aggregationAllowed": false
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
    "scopeNote": "原宿駅周辺と表参道・神宮前の関連地区。港区側も含める候補で、地区境界は未確定。",
    "status": "boundary_and_membership_unverified",
    "aggregationAllowed": false
  },
  {
    "id": "browse_1228ae93dd6b45baac3b3a5a835cfd75",
    "name": "六本木",
    "sourceDistrictIds": [
      "13103007",
      "13103029",
      "13103031"
    ],
    "scopeNote": "六本木地区・六本木ヒルズ・東京ミッドタウンの関連地区。施設と周辺地区の重複は未確認。",
    "status": "boundary_and_membership_unverified",
    "aggregationAllowed": false
  },
  {
    "id": "browse_b1613de41de74eab8f3b2d759d401809",
    "name": "吉祥寺",
    "sourceDistrictIds": [
      "13203001",
      "13203002"
    ],
    "scopeNote": "吉祥寺駅北口・南口の関連地区。地区外の商業活動を含めた街全体の範囲は未確定。",
    "status": "boundary_and_membership_unverified",
    "aggregationAllowed": false
  }
];
export function areaDistricts(asset,area){const ids=new Set(area.sourceDistrictIds);return asset.districts.filter(d=>ids.has(d.source_district_id));}
export function filterAreas(asset,{query='',prefecture='all'}={}){
 const q=query.trim().normalize('NFKC');
 return DISTRICT_AREAS.filter(area=>{const rows=areaDistricts(asset,area);return (prefecture==='all'||rows.some(d=>d.prefecture_code===prefecture))&&(!q||(area.name+' '+rows.map(d=>d.name+' '+d.municipality_name).join(' ')).normalize('NFKC').includes(q));});
}
