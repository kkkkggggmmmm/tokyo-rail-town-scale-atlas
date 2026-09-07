const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const FEATURES = ['買い物', '飲食・夜の街', 'オフィス', '日々の暮らし', '観光・余暇', '商店街', '大型商業施設', '計画的な街づくり'];
const PREFECTURES = ['東京都', '神奈川県', '埼玉県', '千葉県'];
const uniqueCases = cases => [...new Map(cases.map(c => [c.id, c])).values()];

// Counts describe the frozen reference catalog, never measured commercial activity.
export function summarizeCases(cases) {
  const towns = uniqueCases(cases);
  const countLabels = (labels, field) => labels.map(label => ({label, count: towns.filter(c => c[field].includes(label)).length}));
  return {
    total: towns.length,
    features: countLabels(FEATURES, 'features'),
    prefectures: countLabels(PREFECTURES, 'prefectures'),
    multipleStations: towns.filter(c => new Set(c.stations).size > 1).length,
  };
}

export function infographicBase(data, state) {
  return uniqueCases(state.line === 'all' ? data.cases : routeCases(data, state.line));
}

export function infographicCases(data, state) {
  return infographicBase(data, state).filter(c =>
    (!state.feature || c.features.includes(state.feature)) &&
    (!state.prefecture || c.prefectures.includes(state.prefecture)) &&
    (!state.relation || (new Set(c.stations).size > 1) === (state.relation === 'multiple'))
  );
}

export function parseState(hash, data) {
  const p = new URLSearchParams(hash.replace(/^#/, ''));
  const routeIds = data.routes.map(r => r.id);
  const compare = [...new Set((p.get('compare') || '').split(','))].filter(id => routeIds.includes(id)).slice(0, 4);
  return {
    view: ['map', 'profile', 'compare', 'insights'].includes(p.get('view')) ? p.get('view') : 'map',
    line: [...routeIds, 'all'].includes(p.get('line')) ? p.get('line') : routeIds[0],
    q: (p.get('q') || '').slice(0, 100),
    town: data.cases.some(c => c.id === p.get('town')) ? p.get('town') : '',
    compare: compare.length ? compare : [routeIds[0], routeIds[3]],
    feature: FEATURES.includes(p.get('feature')) ? p.get('feature') : '',
    prefecture: PREFECTURES.includes(p.get('prefecture')) ? p.get('prefecture') : '',
    relation: ['multiple', 'single'].includes(p.get('relation')) ? p.get('relation') : '',
  };
}

export function routeCases(data, id) {
  const ids = data.routes.find(r => r.id === id)?.caseIds || [];
  return [...new Set(ids)].map(key => data.cases.find(c => c.id === key)).filter(Boolean);
}

export function visibleCases(data, state) {
  // Search is global, so an anchor station can find its town across route selections.
  const base = state.q.trim() || state.line === 'all' ? data.cases : routeCases(data, state.line);
  const query = state.q.normalize('NFKC').trim().toLocaleLowerCase('ja');
  return base.filter(c => [c.name, ...c.stations].join(' ').normalize('NFKC').toLocaleLowerCase('ja').includes(query));
}

export function commonCases(data, routeIds) {
  if (routeIds.length < 2) return [];
  return data.cases.filter(c => routeIds.every(id => routeCases(data, id).some(x => x.id === c.id)));
}

let DATA, state, drag;
const $ = selector => document.querySelector(selector);
const route = id => DATA.routes.find(r => r.id === id);
function navigate(patch, replace = false) {
  const next = {...state, ...patch};
  const p = new URLSearchParams({view: next.view, line: next.line, compare: next.compare.join(',')});
  if (next.q) p.set('q', next.q);
  if (next.town) p.set('town', next.town);
  for (const key of ['feature', 'prefecture', 'relation']) if (next[key]) p.set(key, next[key]);
  const url = '#' + p.toString();
  if (replace) { history.replaceState(null, '', url); readAndRender(); }
  else if (location.hash !== url) location.hash = url;
}
function readAndRender() { state = parseState(location.hash, DATA); render(); }
function openTown(id) { navigate({town: id}); }
function closeTown() { navigate({town: ''}); }
function lineSelect() {
  return `<div class="select-wrap"><label for="line-select">見る沿線</label><select id="line-select">${['map', 'insights'].includes(state.view) ? `<option value="all" ${state.line === 'all' ? 'selected' : ''}>8沿線を見渡す</option>` : ''}${DATA.routes.map(r => `<option value="${r.id}" ${state.line === r.id ? 'selected' : ''}>${esc(r.shortName)} · ${esc(r.start)}—${esc(r.end)}</option>`).join('')}</select></div>`;
}
function townButton(c, cls = '') {
  return `<button class="${cls}" data-town="${c.id}"><strong>${esc(c.name)}</strong><small>${esc(c.features.slice(0, 2).join(' · ') || '街の特徴を確認')}</small></button>`;
}
function renderMap() {
  const cities = visibleCases(DATA, state);
  const citySet = new Set(cities.map(c => c.id));
  const selectedLine = state.line === 'all' ? null : route(state.line);
  const selectedRouteIds = state.q.trim() ? DATA.routes.filter(r => r.caseIds.some(id => citySet.has(id))).map(r => r.id) : selectedLine ? [selectedLine.id] : DATA.routes.map(r => r.id);
  return `<div class="toolbar">${lineSelect()}<div class="search-wrap"><label class="sr-only" for="search">街・関連する駅名で検索</label><input id="search" type="search" placeholder="街・駅名を探す" autocomplete="off" value="${esc(state.q)}">${state.q ? '<button class="clear-search" id="clear-search" aria-label="検索を消す">×</button>' : ''}</div></div>
  <div class="map-layout"><aside class="panel" aria-label="掲載している街"><div class="panel-top"><h2>${state.q ? '検索結果' : selectedLine ? esc(selectedLine.shortName) : '掲載している街'} <span class="muted">${cities.length}</span></h2><p>${state.q ? '街・関連する駅名で全候補を検索' : '一部の街を選んだ参考リスト'}</p></div>${cities.length ? `<ul class="town-list">${cities.map(c => `<li>${townButton(c)}</li>`).join('')}</ul>` : '<div class="empty"><p>該当する街が見つかりませんでした。</p><button id="reset-search">検索を消して戻る</button></div>'}</aside>
  <section class="map-frame" aria-label="街候補を結ぶ路線概略図"><div class="map-top"><p>路線概略図 <span aria-hidden="true">／</span> 距離縮尺なし</p><div class="map-controls"><button id="zoom-in" aria-label="図を拡大">＋</button><button id="zoom-out" aria-label="図を縮小">−</button><button id="fit-map" class="fit">見渡す</button></div></div>
  <svg class="map-canvas" id="route-map" viewBox="0 0 1650 1150" xmlns="http://www.w3.org/2000/svg" role="group" aria-label="街候補の位置関係を示す概略図。各点を選択できます。">
  <defs><pattern id="grid" width="35" height="35" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="#dce4d8"/></pattern></defs><rect x="-10000" y="-10000" width="20000" height="20000" fill="url(#grid)"/>
  ${DATA.routes.map(r => { const active = selectedRouteIds.includes(r.id), pts = routeCases(DATA, r.id); return `<polyline class="route-path" points="${pts.map(c => `${c.x},${c.y}`).join(' ')}" stroke="${r.color}" stroke-width="${active ? 5 : 2}" opacity="${active ? .8 : .1}"/>`; }).join('')}
  ${DATA.cases.map(c => { const active = citySet.has(c.id); return `<g class="town-marker" data-town="${c.id}" transform="translate(${c.x} ${c.y})" ${active ? 'role="button" tabindex="0"' : 'aria-hidden="true" style="pointer-events:none"'} aria-label="${esc(c.name)}の詳細" opacity="${active ? 1 : .14}"><title>${esc(c.name)}</title><circle r="23" fill="transparent"/><circle class="dot" r="8" stroke="${selectedLine?.color || '#486a54'}" stroke-width="3" fill="#fff"/>${active ? `<text x="0" y="${c.id === 'GE023' ? 36 : -22}" text-anchor="middle">${esc(c.name)}</text>` : ''}</g>`; }).join('')}
  </svg><div class="map-caption"><span><i class="legend-dot"></i>街候補 · 点の大きさは共通</span><span class="drag-hint">ドラッグで移動 · ＋／−で拡大縮小</span></div></section></div>
  <div class="route-key" aria-label="路線の凡例">${DATA.routes.map(r => `<button data-map-line="${r.id}" style="--route:${r.color}"><i class="line-swatch"></i>${esc(r.shortName)}</button>`).join('')}</div>`;
}
function renderProfile() {
  const r = route(state.line) || DATA.routes[0], cities = routeCases(DATA, r.id);
  return `<div class="toolbar">${lineSelect()}</div><section class="profile-panel" style="--route:${r.color}"><div class="profile-head"><div><p class="eyebrow">LINE PROFILE</p><h2>${esc(r.shortName)}</h2><p>${esc(r.start)} → ${esc(r.end)}　のうち掲載した街</p></div><span class="count-pill"><b>${cities.length}</b>掲載候補</span></div><p class="reference-note">掲載候補だけを順に並べています。番号は駅番号ではなく、間隔も駅間距離を表しません。</p><ol class="profile-list">${cities.map((c, i) => `<li class="profile-row"><span class="seq" aria-hidden="true">${String(i + 1).padStart(2, '0')}</span><button class="profile-town" data-town="${c.id}"><strong>${esc(c.name)} <span aria-hidden="true" style="display:inline">↗</span></strong><span>${esc(c.features.join(' · '))}</span></button><div class="scale-missing"><span>商業規模</span>未算定</div></li>`).join('')}</ol><p class="profile-footer">${esc(r.note)}</p></section>`;
}
function renderCompare() {
  const common = commonCases(DATA, state.compare);
  return `${insightNav()}<p class="compare-intro">2〜4沿線を選び、掲載した街の顔ぶれを見比べます。掲載数は調査候補の選び方によって異なり、街の多さ・沿線の充実度を表しません。</p><div class="compare-options" role="group" aria-label="比較する沿線（2〜4本）">${DATA.routes.map(r => `<label><input type="checkbox" value="${r.id}" ${state.compare.includes(r.id) ? 'checked' : ''} ${state.compare.length >= 4 && !state.compare.includes(r.id) ? 'disabled' : ''}><span>${esc(r.shortName)}</span></label>`).join('')}</div>${state.compare.length < 2 ? '<p class="notice" role="status">比較する沿線を、もう1本選んでください。</p>' : ''}<div class="compare-grid">${state.compare.map(id => { const r = route(id), cities = routeCases(DATA, id); return `<section class="compare-card" style="--route:${r.color}"><h2>${esc(r.shortName)}</h2><p class="endpoint">${esc(r.start)} — ${esc(r.end)}</p><p class="compare-count"><b>${cities.length}</b> このリストの掲載候補</p><ul class="mini-towns">${cities.map(c => `<li><button data-town="${c.id}">${esc(c.name)}</button></li>`).join('')}</ul><h3 class="comparison-heading">参考特徴の内訳</h3>${comparisonBars(cities)}<p class="reference-note">商業規模・中心地間の距離：未算定</p><button class="open-route" data-profile-line="${r.id}">この沿線をたどる →</button></section>`; }).join('')}</div>${state.compare.length >= 2 ? `<aside class="common"><p><strong>選んだ全沿線に共通して掲載する街</strong><br>${common.length ? common.map(c => `<button data-town="${c.id}">${esc(c.name)}</button>`).join(' ') : 'この候補リストにはありません。実際の接続関係を網羅した結果ではありません。'}</p></aside>` : ''}`;
}
function insightNav() {
  return `<div class="insight-nav" aria-label="図と比較の表示"><button data-insights aria-pressed="${state.view === 'insights'}">候補データを図で見る</button><button data-view="compare" aria-pressed="${state.view === 'compare'}">沿線を並べて比較</button></div>`;
}
function countBars(summary, field, filterKey) {
  return `<div class="count-bars">${summary[field].map(({label, count}) => `<button class="count-bar" data-filter-key="${filterKey}" data-filter-value="${esc(label)}" aria-pressed="${state[filterKey] === label}"><span class="bar-label">${esc(label)}</span><span class="bar-number"><b>${count}</b> / ${summary.total}候補</span><span class="bar-track" aria-hidden="true"><span style="width:${summary.total ? count / summary.total * 100 : 0}%"></span></span></button>`).join('')}</div>`;
}
function stationBridge(c, interactive = true) {
  return `<div class="station-bridge"><ul aria-label="候補に登録された関連駅">${[...new Set(c.stations)].map(name => `<li>${esc(name)}</li>`).join('')}</ul><span class="bridge-caption">これらの駅と関連づけた街候補</span><${interactive ? `button data-town="${c.id}"` : 'div'} class="bridge-town">${esc(c.name)}<small>${interactive ? '街の詳細を見る →' : '調査対象の街候補'}</small></${interactive ? 'button' : 'div'}></div>`;
}
function comparisonBars(cities) {
  const summary = summarizeCases(cities);
  return `<div class="comparison-bars" aria-label="参考特徴ごとの掲載候補数">${summary.features.map(({label, count}) => `<div><span>${esc(label)}</span><b>${count} / ${summary.total}</b><span class="bar-track" aria-hidden="true"><span style="width:${summary.total ? count / summary.total * 100 : 0}%"></span></span></div>`).join('')}</div><p class="reference-note">分母はこの沿線の掲載候補数。複数の特徴を持つ街は各項目に含みます。</p>`;
}
function renderInfographics() {
  const base = infographicBase(DATA, state), summary = summarizeCases(base), matches = infographicCases(DATA, state);
  const example = matches.find(c => new Set(c.stations).size > 1) || matches[0];
  const scope = state.line === 'all' ? '8沿線の掲載候補' : route(state.line).shortName + 'の掲載候補';
  const activeFilters = [state.feature, state.prefecture, state.relation === 'multiple' ? '関連駅が複数' : state.relation === 'single' ? '関連駅が1つ' : ''].filter(Boolean);
  return `${insightNav()}<div class="toolbar">${lineSelect()}<p class="infographic-intro">街の参考リストを集計しました。<br>図の項目を押すと、該当する街を確認できます。</p></div>
    <section class="summary-banner" aria-label="集計対象"><div><p class="eyebrow">REFERENCE CATALOG</p><h2>${esc(scope)}</h2><p>同じ街が複数の沿線に載っていても、ここでは1候補として数えます。</p></div><div class="summary-total"><b>${summary.total}</b><span>重複を除いた街候補</span></div></section>
    <div class="infographic-grid"><section class="info-card feature-card"><p class="figure-number">01 / 街の特徴</p><h2>どんな特徴が挙がっている？</h2><p class="chart-note">候補選定時の参考メモの内訳です。複数回答のため、件数の合計は${summary.total}を超えることがあります。</p>${countBars(summary, 'features', 'feature')}<p class="chart-footnote">棒の全幅 = 掲載候補${summary.total}件。商業規模・売上・人気の評価ではありません。</p></section>
    <section class="info-card prefecture-card"><p class="figure-number">02 / 掲載エリア</p><h2>どの都県を見ている？</h2><p class="chart-note">この参考リストに掲載した街の件数です。都県内にある全中心地の数ではありません。</p>${countBars(summary, 'prefectures', 'prefecture')}<p class="chart-footnote">候補の選び方が件数に影響します。</p></section>
    <section class="info-card station-card"><p class="figure-number">03 / 街と駅の関係</p><h2>ひとつの街に、複数の駅。</h2><p class="relation-total"><b>${summary.multipleStations}</b><span> / ${summary.total}候補に<br>複数の関連駅を登録</span></p><div class="waffle" aria-hidden="true">${Array.from({length:summary.total}, (_, i) => `<span class="${i < summary.multipleStations ? 'filled' : ''}"></span>`).join('')}</div><p class="chart-note">1マス = 1候補。塗りつぶしは関連駅が複数の候補です。駅の多さは街の大きさや交通力の評価ではありません。</p><div class="relation-filters"><button data-filter-key="relation" data-filter-value="multiple" aria-pressed="${state.relation === 'multiple'}">複数の駅がある候補</button><button data-filter-key="relation" data-filter-value="single" aria-pressed="${state.relation === 'single'}">駅が1つの候補</button></div></section></div>
    <section class="matching-section" aria-labelledby="matching-title"><div class="matching-head"><div><p class="eyebrow">EXPLORE THE DATA</p><h2 id="matching-title">図のもとになった街を見る</h2><p role="status">${activeFilters.length ? esc(activeFilters.join(' × ')) : esc(scope)}：<strong>${matches.length}候補</strong></p></div>${activeFilters.length ? '<button id="clear-filters">絞り込みを解除</button>' : ''}</div><p class="chart-note">図は上で選んだ沿線の全候補を示し、以下のリストだけを条件の掛け合わせで絞り込みます。</p>${matches.length ? `<ul class="matching-towns">${matches.map(c => `<li>${townButton(c, 'matching-town')}</li>`).join('')}</ul>` : '<p class="empty">この組み合わせに該当する掲載候補はありません。絞り込みを解除して確認できます。</p>'}</section>
    ${example ? `<section class="info-card connection-example"><div><p class="figure-number">駅名から街を探すために</p><h2>例えば、${esc(example.name)}では。</h2><p class="chart-note">候補に登録された駅名と街の対応を図にしました。駅の配置や乗換経路を示す図ではありません。</p><p class="chart-note">同一駅・改札内乗換の認定や、商業中心地の境界確定は含みません。</p></div>${stationBridge(example)}</section>` : ''}
    <aside class="data-provenance"><strong>この図のデータ</strong><p>2026年8月30日に固定した街候補リストと代表沿線リスト。対象は1都3県の公開参考候補${DATA.cases.length}件です。棒やマスはこのリストの件数から計算しています。</p><p>商業統計・駅別乗降客数・人口・地価の数値は未接続です。商業規模、交通力、街の境界と推定の信頼度は、引き続き未算定・未評価です。</p></aside>`;
}
function renderDetail() {
  const c = DATA.cases.find(x => x.id === state.town), dialog = $('#detail');
  if (!c) { if (dialog.open) dialog.close(); return; }
  $('#detail-content').innerHTML = `<div class="dialog-head"><p class="eyebrow">TOWN NOTE</p><button class="icon-button" id="close-town" aria-label="街の詳細を閉じる">×</button></div><p class="detail-region">${esc(c.prefectures.join('・'))} · 街候補</p><h2 id="detail-title">${esc(c.name)}</h2><p class="stations">関連する駅：${esc(c.stations.join(' ／ '))}</p><h3>この街を読む手がかり</h3><div class="tags">${c.features.map(t => `<span class="tag">${esc(t)}</span>`).join('')}</div><p class="reference-note">候補選定時の参考メモです。統計で確定した分類ではありません。</p><dl class="metric-grid"><div><dt>商業規模</dt><dd>未算定<small>お店・働く人の集積</small></dd></div><div><dt>交通力</dt><dd>未算定<small>駅の利用・結節性</small></dd></div><div><dt>中心地の境界</dt><dd>未確定<small>点は境界を示しません</small></dd></div><div><dt>推定の信頼度</dt><dd>未評価<small>低評価・0の意味ではありません</small></dd></div></dl><h3>駅名と街の対応</h3>${stationBridge(c, false)}<h3>掲載している沿線をたどる</h3><div class="detail-actions">${DATA.routes.filter(r => r.caseIds.includes(c.id)).map(r => `<button style="--route:${r.color}" data-profile-line="${r.id}">${esc(r.shortName)} →</button>`).join('')}</div><p class="reference-note">関連駅は同一駅・改札内乗換を意味しません。<br>参考リスト：2026年8月30日固定</p>`;
  $('#close-town').onclick = closeTown;
  if (!dialog.open) dialog.showModal();
}
function fitMap() {
  const svg = $('#route-map'); if (!svg) return;
  const cities = visibleCases(DATA, state); if (!cities.length) return;
  const minX = Math.min(...cities.map(c => c.x)), maxX = Math.max(...cities.map(c => c.x));
  const minY = Math.min(...cities.map(c => c.y)), maxY = Math.max(...cities.map(c => c.y));
  const ratio = svg.clientWidth / svg.clientHeight || 1.5;
  let w = Math.max(420, maxX - minX + 330), h = Math.max(320, maxY - minY + 240);
  if (w / h > ratio) h = w / ratio; else w = h * ratio;
  svg.setAttribute('viewBox', `${(minX + maxX - w) / 2} ${(minY + maxY - h) / 2} ${w} ${h}`);
}
function zoom(factor) {
  const svg = $('#route-map'), b = svg.viewBox.baseVal;
  const w = Math.min(4500, Math.max(220, b.width * factor)), h = w * b.height / b.width;
  svg.setAttribute('viewBox', `${b.x + (b.width - w) / 2} ${b.y + (b.height - h) / 2} ${w} ${h}`);
}
function mapEvents() {
  const svg = $('#route-map'); if (!svg) return;
  $('#zoom-in').onclick = () => zoom(.75); $('#zoom-out').onclick = () => zoom(1.33); $('#fit-map').onclick = fitMap;
  svg.addEventListener('pointerdown', e => { if (e.target.closest('[data-town]')) return; drag = {id:e.pointerId,x:e.clientX,y:e.clientY,box:svg.getAttribute('viewBox').split(' ').map(Number)}; svg.setPointerCapture(e.pointerId); });
  svg.addEventListener('pointermove', e => { if (!drag || e.pointerId !== drag.id) return; const [x,y,w,h]=drag.box; svg.setAttribute('viewBox', `${x-(e.clientX-drag.x)*w/svg.clientWidth} ${y-(e.clientY-drag.y)*h/svg.clientHeight} ${w} ${h}`); });
  svg.addEventListener('pointerup', () => {drag=null;}); svg.addEventListener('pointercancel', () => {drag=null;});
  requestAnimationFrame(fitMap);
}
function render() {
  const focused = document.activeElement?.id === 'search';
  const cursor = focused ? document.activeElement.selectionStart : null;
  const filterFocus = document.activeElement?.dataset.filterKey ? {...document.activeElement.dataset} : null;
  $('#page-title').textContent = ({map:'次の街は、どんな街だろう。',profile:'沿線に並ぶ、街の顔ぶれ。',compare:'暮らしの舞台を、見比べる。',insights:'街の手がかりを、図で読む。'})[state.view];
  document.querySelectorAll('.tabs [data-view]').forEach(b => b.setAttribute('aria-current', b.dataset.view === (state.view === 'insights' ? 'compare' : state.view) ? 'page' : 'false'));
  $('#app').innerHTML = state.view === 'map' ? renderMap() : state.view === 'profile' ? renderProfile() : state.view === 'insights' ? renderInfographics() : renderCompare();
  if ($('#line-select')) $('#line-select').onchange = e => navigate({line:e.target.value,q:'',feature:'',prefecture:'',relation:''});
  if ($('#search')) $('#search').oninput = e => navigate({q:e.target.value}, true);
  if ($('#clear-search')) $('#clear-search').onclick = () => navigate({q:''}, true);
  if ($('#reset-search')) $('#reset-search').onclick = () => navigate({q:''}, true);
  document.querySelectorAll('.compare-options input').forEach(input => { input.onchange = e => {const ids=e.target.checked?[...state.compare,input.value]:state.compare.filter(id=>id!==input.value);navigate({compare:ids});}; });
  if (focused && $('#search')) { $('#search').focus(); if (cursor !== null) $('#search').setSelectionRange(cursor,cursor); }
  if ($('#clear-filters')) $('#clear-filters').onclick = () => navigate({feature:'',prefecture:'',relation:''});
  if (filterFocus) [...document.querySelectorAll('[data-filter-key]')].find(b => b.dataset.filterKey === filterFocus.filterKey && b.dataset.filterValue === filterFocus.filterValue)?.focus({preventScroll:true});
  mapEvents(); renderDetail();
}
async function boot() {
  try {
    const response = await fetch('./data.json'); if (!response.ok) throw new Error('データを読み込めませんでした。');
    DATA = await response.json();
    if (DATA.cases.length !== 44 || DATA.routes.length !== 8) throw new Error('掲載データを確認できませんでした。');
    window.addEventListener('hashchange', readAndRender);
    window.addEventListener('resize', fitMap);
    document.addEventListener('click', e => {
      const town=e.target.closest('[data-town]'); if(town){openTown(town.dataset.town);return;}
      const insights=e.target.closest('[data-insights]');if(insights){navigate({view:'insights',line:'all',q:'',town:'',feature:'',prefecture:'',relation:''});return;}
      const filter=e.target.closest('[data-filter-key]');if(filter){const key=filter.dataset.filterKey; navigate({[key]:state[key] === filter.dataset.filterValue ? '' : filter.dataset.filterValue});return;}
      const profile=e.target.closest('[data-profile-line]');if(profile){navigate({view:'profile',line:profile.dataset.profileLine,town:'',q:''});return;}
      const map=e.target.closest('[data-map-line]');if(map){navigate({view:'map',line:map.dataset.mapLine,town:'',q:''});return;}
      const view=e.target.closest('[data-view]');if(view)navigate({view:view.dataset.view,line:state.line==='all'&&view.dataset.view==='profile'?DATA.routes[0].id:state.line,town:'',q:''});
    });
    document.addEventListener('keydown', e => { const town=e.target.closest('.town-marker[data-town]');if(town&&['Enter',' '].includes(e.key)){e.preventDefault();openTown(town.dataset.town);} });
    $('#detail').addEventListener('cancel', e => {e.preventDefault();closeTown();});
    $('#about-button').onclick = $('#method-link').onclick = () => $('#about').showModal();
    $('[data-close="about"]').onclick = () => $('#about').close();
    readAndRender();
  } catch (err) {
    $('#app').innerHTML = `<div class="empty" role="alert"><p>${esc(err.message)}</p><button id="reload">もう一度読み込む</button></div>`;
    $('#reload').onclick = () => location.reload();
  }
}
if (typeof document !== 'undefined') boot();
