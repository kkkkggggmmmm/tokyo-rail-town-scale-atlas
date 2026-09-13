// Ordered pilot corridors and formal N02 routes are deliberately separate.
export const belongsToRoute=(station,id)=>(station.routeIds||[]).includes(id)||(station.networkRouteIds||[]).includes(id);
export const allRoutes=data=>[...data.routes,...(data.officialRoutes||[])];
export function mergeNetworkData(base,network){
 const ids=new Set(base.stations.map(s=>s.id));
 if(network.stations.some(s=>ids.has(s.id)))throw Error('追加駅のIDが既存駅と重複しています。');
 const stations=[...base.stations,...network.stations].map(s=>({...s,networkRouteIds:network.stationMemberships[s.id]||[]}));
 if(new Set(stations.map(s=>s.id)).size!==stations.length)throw Error('駅IDが重複しています。');
 if(stations.length!==network.coverage.stationCount)throw Error('駅の収録件数が一致しません。');
 const groups=new Map();
 for(const s of stations){if(groups.has(s.groupId)&&groups.get(s.groupId)!==s.officialRouteCount)throw Error('同じ駅群の路線数が一致しません。');groups.set(s.groupId,s.officialRouteCount);}
 return {...base,stations,meshContexts:{...network.meshContexts,...base.meshContexts},officialRoutes:network.officialRoutes,
  networkScope:network.scope,networkCoverage:network.coverage,networkSources:network.sourceArtifacts};
}
export function comparisonRoute(data,station,line){
 const routes=allRoutes(data);
 return routes.find(r=>r.id===line&&belongsToRoute(station,r.id))||routes.find(r=>belongsToRoute(station,r.id));
}
export function stationCaption(data,station){
 const names=(data.officialRoutes||[]).filter(r=>(station.networkRouteIds||[]).includes(r.id)).map(r=>r.name);
 return station.operator+(names.length?' · '+names.join('・'):'');
}
export function routeDestination(data,id){return data.routes.some(r=>r.id===id)?{view:'line',line:id,from:0,to:null}:{view:'map',line:id,sort:'name',dir:'asc',page:1,station:''};}
