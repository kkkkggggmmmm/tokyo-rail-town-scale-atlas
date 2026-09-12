import {DISTRICT_AREAS,filterAreas,rankAreas} from './district-areas.mjs';
import {studentShare,filterDistricts,districtTotal,moneyLabel,DISTRICT_METRICS,rankDistricts} from './supplements.mjs';
const PREF={'11':'埼玉県','12':'千葉県','13':'東京都','14':'神奈川県'};
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const num=v=>Number.isFinite(v)?new Intl.NumberFormat('ja-JP',{maximumFractionDigits:1}).format(v):'—';
const link=(url,label='公式データ')=>`<a class="source" href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(label)} ↗</a>`;

export function studentSection(data,students,station){
 const components=students.meshContexts[station.meshCode]?.components||[];
 return `<h2 class="section-label">学生が暮らす街か</h2><p class="scope-label">2020年10月1日・駅のある約500m区画の都県別公表分。ここに住む大学・大学院の在学者を数えています。大学へ通ってくる学生数は含みません。</p>${components.map(c=>{
  const source=students.sources.find(x=>x.id===c.sourceId),share=studentShare(data,students,station,c.prefectureCode);
  const combined=String(c.processingCode)==='1'||c.aggregationTarget||c.aggregatedSourceMeshCodes;
  const count=Number.isFinite(c.university?.value)?num(c.university.value):'非公表・秘匿';
  return `<h3 class="section-label">${esc(PREF[c.prefectureCode])}の公表分</h3><div class="metric-grid"><div class="metric"><span class="metric-label">大学・大学院在学者${combined?'（合算値）':''}</span><div class="metric-value">${count}<span class="unit">${Number.isFinite(c.university?.value)?'人':''}</span></div><small>居住地で集計 ${link(source?.url)}</small></div><div class="metric"><span class="metric-label">住民に占める割合</span><div class="metric-value ${share===null?'unavailable':''}">${share===null?'算定不可':num(share)}${share===null?'':'<span class="unit">%</span>'}</div><small>在学者数 ÷ 同じ区画の総人口</small></div></div>${share===null?'<p class="note">秘匿・合算・都県境・分母未取得などで同じ範囲の比率を確定できない場合、割合は表示しません。</p>':`<div class="student-share-bar" role="img" aria-label="住民のうち大学・大学院在学者 ${num(share)}%"><span style="width:${share}%"></span></div><p class="note">棒の全体が住民100%。色の部分が大学・大学院在学者です。</p>`}${combined?'<p class="scope-label">複数区画の合算対象です。この人数を単一区画の値として沿線比較には使いません。</p>':''}<details><summary>高校・短大などの在学者と定義</summary><p>短大・高専：${num(c.juniorCollege?.value)} 人／高校：${num(c.highSchool?.value)} 人。いずれも居住者です。</p><p>${esc(students.interpretation.definitionNote)} ${link(students.interpretation.definitionUrl,'国勢調査の学校区分')}</p></details>`;
 }).join('')||'<p class="note">この区画の在学者数は未取得です。</p>'}`;
}

function districtHeaders(sort,dir){
 return Object.entries(DISTRICT_METRICS).map(([key,m])=>{
  const active=sort===key,next=active&&dir==='desc'?'小さい順':'大きい順';
  return `<th scope="col" aria-sort="${active?(dir==='asc'?'ascending':'descending'):'none'}"><button type="button" class="district-sort" id="district-sort-${key}" data-district-sort="${key}" aria-label="${m.label}を${next}に並べ替え"><span>${m.label} <span class="sort-arrow" aria-hidden="true">${active?(dir==='asc'?'↑':'↓'):'↕'}</span><small>${m.unit}</small></span></button></th>`;
 }).join('');
}

export function districtView(asset,{query='',prefecture='all',sort='source',dir='desc'}={}){
 const ranked=Object.hasOwn(DISTRICT_METRICS,sort);
 const headers=districtHeaders(sort,dir);
 return `<div class="section-heading"><div><div class="eyebrow">COMMERCIAL DISTRICT / SALES</div><h2>公表地区の数値を確認する</h2><p>1都3県・公式商業集積地区 ${num(asset.districts.length)}地区。売上は2020年の年間額です。</p></div></div><p class="scope-label">この表は街全体のランキングではありません。地域・駅の出口・商店街・施設など、範囲の異なる公表地区を並べています。GDPは「付加価値」、ここで表示するのは「売上」です。小売・飲食サービス・生活関連サービスの3業種を掲載しています。2020年はコロナ期のため、現在の売上とは異なります。</p><div class="data-search"><label>地区名・市区町村名<input id="district-query" type="search" value="${esc(query)}" placeholder="銀座、吉祥寺、新宿など" maxlength="80"></label><label>都県<select id="district-pref"><option value="all" ${prefecture==='all'?'selected':''}>1都3県すべて</option>${Object.entries(PREF).map(([code,name])=>`<option value="${code}" ${prefecture===code?'selected':''}>${name}</option>`).join('')}</select></label></div><div class="district-sort-info"><p id="district-result-count" class="note" role="status" aria-live="polite"></p>${ranked?'<button type="button" data-district-sort="source">地域順に戻す</button>':''}</div><p id="district-sort-help" class="note">指標名をタップして大きい順に。もう一度タップすると小さい順に切り替わります。順位は選択中の都県・検索条件内で、同じ公表値は同順位です。秘匿・未公表は順位を付けず末尾に表示します。「単位未満」は原表の丸め値で並べます。</p><div class="table-wrap" id="district-table-scroll"><table class="district-table" aria-describedby="district-sort-help"><thead><tr>${ranked?'<th scope="col" class="district-rank">順位</th>':''}<th scope="col">公式商業地区名・所在地</th>${headers}</tr></thead><tbody id="district-results"></tbody></table></div><button id="district-more" class="more-button">次の30地区を表示</button><p class="note">地区名は統計の原表に従います。駅ビルや商店街が別地区になる場合があります。例えば「新宿駅東口」は新宿全体ではありません。地区の境界を駅や本アプリの中心地に結び付けていないため、沿線の合計・総合評価には加えていません。</p><details class="card"><summary>売上の集計範囲・記号・出典</summary><p>3業種売上計は、3つの売上すべてが公表されている地区だけ計算しています。全産業の総売上ではありません。「秘匿」は公表が伏せられた値、「—」は該当数字なし・未公表などです。原表の0は百万円未満のため「単位未満」と表示し、これを含む合計に「約」を付けます。</p><p>飲食サービスは産業76・77。生活関連サービスは78・79のうち対象業種で、娯楽業80を含みません。小売売場面積は法人の小売業が対象で、オフィス面積ではありません。面積の基準日は2021年6月1日です。</p><p>総務省・経済産業省「令和3年経済センサス‐活動調査 立地環境特性編 第2表」を駅まちアトラスが加工。公表日2024年6月25日。${link(asset.source.url)} ${link(asset.source.definition_url,'集計定義')} ${link(asset.source.terms_url,'利用条件')}</p></details>`;
}

export function districtRows(asset,{query='',prefecture='all',limit=30,sort='source',dir='desc'}={}){
 const {rows,ranked,eligible}=rankDistricts(asset.districts,{query,prefecture,sort,dir}),shown=rows.slice(0,limit);
 const html=shown.map(({district:d,rank})=>{
  const m=d.metrics,total=districtTotal(d),rounded=['retail_sales_million_yen','food_service_sales_million_yen','personal_service_sales_million_yen'].some(k=>m[k].status==='below_rounding_unit');
  const totalLabel=total===null?'—':total===0&&rounded?'単位未満':(rounded?'約 ':'')+moneyLabel({value:total,status:'observed'});
  return `<tr>${ranked?`<td class="district-rank">${rank===null?'—':num(rank)}</td>`:''}<td class="district-name"><strong>${esc(d.name)}</strong><small>${esc(PREF[d.prefecture_code])} ${esc(d.municipality_name)}／地区 ${esc(d.source_district_id)}</small></td>${['retail_sales_million_yen','food_service_sales_million_yen','personal_service_sales_million_yen'].map(k=>`<td class="number-cell">${moneyLabel(m[k])}</td>`).join('')}<td class="number-cell"><b>${totalLabel}</b></td><td class="number-cell">${m.retail_sales_floor_sqm.status==='suppressed'?'秘匿':num(m.retail_sales_floor_sqm.value)}</td></tr>`;
 }).join('')||`<tr><td colspan="${ranked?7:6}">該当する地区はありません。別の地区名・市区町村名で検索してください。</td></tr>`;
 return {html,total:rows.length,shown:shown.length,ranked,eligible};
}

export function cafeView(asset,{query=''}={}){
 return `<div class="section-heading"><div><div class="eyebrow">CAFES / MUNICIPALITY</div><h2>喫茶店・カフェは、何店あるか</h2><p>2021年6月1日・民営事業所。市区町村・政令市の区全体の件数です。</p></div></div><p class="scope-label">この数字は自治体全体の喫茶店数です。駅周辺の店舗数とは区別して表示します。スナックバーは含みません。</p><div class="data-search"><label>市区町村名<input id="cafe-query" type="search" value="${esc(query)}" placeholder="新宿区、武蔵野市、横浜市など" maxlength="80"></label></div><p id="cafe-result-count" class="note" role="status"></p><div class="table-wrap"><table class="cafe-table"><thead><tr><th>集計地域</th><th>喫茶店数<br>店・2021年</th></tr></thead><tbody id="cafe-results"></tbody></table></div><button id="cafe-more" class="more-button">次の30地域を表示</button><p class="note">258地域のうち252地域で数値を確認済みです。数値を確定できない6地域は空欄のまま保存し、この一覧には含めていません。政令市の合計と各区は範囲が重なるため合算しません。</p><details class="card"><summary>喫茶店の定義・出典</summary><p>${esc(asset.source.definition)}</p><p>総務省・経済産業省「令和3年経済センサス‐活動調査 表9-3」を駅まちアトラスが加工。産業小分類767、経営組織「うち民営」、従業者規模「総数」を選択。公表日2023年6月27日。${link(asset.source.landing_url)} ${link(asset.source.definition_url,'産業分類')} ${link(asset.source.terms_url,'利用条件')}</p></details>`;
}

export function cafeRows(asset,{query='',limit=30}={}){
 const q=query.trim().normalize('NFKC'),rows=asset.observations.filter(r=>r.approved_for_display&&Number.isFinite(r.value)&&(!q||(r.area_name+' '+PREF[r.area_code.slice(0,2)]).normalize('NFKC').includes(q))),shown=rows.slice(0,limit);
 return {total:rows.length,shown:shown.length,html:shown.map(r=>`<tr><td><strong>${esc(r.area_name)}</strong><small>${esc(PREF[r.area_code.slice(0,2)])}／地域コード ${esc(r.area_code)}</small></td><td class="number-cell">${num(r.value)}</td></tr>`).join('')||'<tr><td colspan="2">数値を確認済みの地域に該当するものはありません。</td></tr>'};
}

function areaValue(result,key){
 const m=result.metrics[key],unit=key==='total'?'項目':'地区';
 if(!m.complete)return `<span class="unavailable">—</span><small>${result.identityValid?`${m.observed}/${m.expected}${unit}のみ公表`:'集計対象を要確認'}</small>`;
 const value=key==='retail_sales_floor_sqm'?num(m.value):moneyLabel({value:m.value,status:'observed'});
 return `<b>${m.rounded?'約 ':''}${value}</b><small>${m.observed}/${m.expected}${unit}を合計</small>`;
}
const STATUS_NAMES={suppressed:'秘匿',not_applicable:'該当数字なし',not_acquired:'未取得',source_row_missing:'原表行なし',duplicate_source_id:'原表ID重複'};

export function districtAreaView(asset,{query='',prefecture='all',areaId='',sort='retail_sales_million_yen',dir='desc'}={}){
 const areas=filterAreas(asset,{query,prefecture}),selected=areas.find(a=>a.id===areaId)||areas[0];
 const ranking=rankAreas(asset,{query,prefecture,sort,dir}),chosen=ranking.rows.find(r=>r.area.id===selected?.id),key=ranking.sort;
 const rows=chosen?.districts||[];
 const omitted=chosen?Object.entries(chosen.metrics).filter(([k,m])=>k!=='total'&&!m.complete).flatMap(([k,m])=>m.missing.map(x=>`<li>${esc(x.name)}：${esc(DISTRICT_METRICS[k].label)}（${esc(STATUS_NAMES[x.status]||x.status)}）</li>`)).join(''):'';
 const table=ranking.rows.map(r=>`<tr ${r.area.id===selected?.id?'class="area-selected"':''}><td class="district-rank">${r.rank??'—'}</td><th scope="row" class="district-name"><button type="button" id="area-${r.area.id}" data-district-area="${r.area.id}" aria-pressed="${r.area.id===selected?.id}" aria-label="${esc(r.area.name)}の集計地区・内訳を見る">${esc(r.area.name)}<small>${r.area.sourceDistrictIds.length}地区・内訳を見る</small></button></th>${Object.keys(DISTRICT_METRICS).map(k=>`<td class="number-cell">${areaValue(r,k)}</td>`).join('')}</tr>`).join('');
 return `<div class="section-heading"><div><div class="eyebrow">AREA TOTALS / RANKING</div><h2>エリア合計・ランキング</h2><p>東口・西口などをまとめて、街ごとの商業活動を比べる。</p></div></div>
 <p class="scope-label">先行${DISTRICT_AREAS.length}エリア（東京都）。各エリアに定義した公表地区すべての合計です。地区外の店舗を含む地理的な街全域の総額ではありません。集計範囲は地域名をタップして確認できます。</p>
 <div class="data-search"><label>街・地区名<input id="district-query" type="search" value="${esc(query)}" placeholder="新宿、銀座、吉祥寺など" maxlength="80"></label><label>都県<select id="district-pref"><option value="all" ${prefecture==='all'?'selected':''}>1都3県すべて</option>${Object.entries(PREF).map(([code,name])=>`<option value="${code}" ${prefecture===code?'selected':''}>${name}</option>`).join('')}</select></label></div>
 ${!selected?'<div class="empty"><p>この条件のエリア合計はまだ作成されていません。</p><button type="button" data-district-mode="source">公表地区の全データを見る</button></div>':`
 <p class="note" role="status" aria-live="polite">${ranking.rows.length}エリア中、${DISTRICT_METRICS[key].label}の順位対象 ${ranking.eligible}エリア／合計不可 ${ranking.rows.length-ranking.eligible}エリア。${dir==='asc'?'小さい順':'大きい順'}で表示中。</p>
 <p id="area-sort-help" class="note">指標名をタップして並べ替え。もう一度で順序を反転します。同じ公表値は同順位。秘匿・未公表を含む合計には順位を付けません。検索はエリアを絞り込み、合計対象の地区は減らしません。</p>
 <div class="table-wrap" id="district-table-scroll" tabindex="-1"><table class="district-table area-ranking" aria-describedby="area-sort-help"><caption class="sr-only">選択中の条件に一致するエリアの公表地区合計</caption><thead><tr><th scope="col" class="district-rank">順位</th><th scope="col" class="district-name">エリア・集計範囲</th>${districtHeaders(key,dir)}</tr></thead><tbody>${table}</tbody></table></div>
 <section class="area-detail" id="area-detail" tabindex="-1"><div class="section-heading"><div><h3>${esc(selected.name)}の集計範囲・内訳</h3><p>以下の${rows.length}公表地区が、このエリアの合計対象です。</p></div><button type="button" data-area-ranking>ランキングへ戻る ↑</button></div><p>${esc(selected.scopeNote)}</p>
 ${omitted?`<div class="area-missing"><b>合計できない項目</b><p>以下の値が欠けるため、該当する業種と3業種売上計は算出していません。</p><ul>${omitted}</ul></div>`:''}
 <details><summary>${esc(selected.name)}の全${rows.length}地区の数値を開く</summary><div class="table-wrap"><table class="district-table"><thead><tr><th scope="col">合計対象の公表地区・所在地</th>${Object.values(DISTRICT_METRICS).map(m=>`<th scope="col">${m.label}<small>${m.unit}</small></th>`).join('')}</tr></thead><tbody>${districtRows({districts:rows},{limit:rows.length}).html}</tbody></table></div></details></section>`}
 <details class="card area-method"><summary>合計・順位の計算方法と出典</summary><p>公表表の商業集積地区コードを各エリアに対応付け、対象の地区すべてを加算した集計値です。原表の市区町村・都道府県総計は加えません。同じ地区コードを複数エリアへ重複加算しません。範囲は本アプリで定義した地区の組み合わせで、行政区全体や確定済みの商業中心地ポリゴンではありません。</p><p>全地区の対象値が公表されている項目だけ合計します。3業種売上計には全地区・3業種すべての公表値が必要です。「秘匿」「該当数字なし」「未取得」を0に置き換えません。数値が欠けたエリアは末尾に置き、順位を付けません。同額は同順位（1、1、3）。対象は表示条件内の先行エリアで、東京圏の全地域ランキングではありません。</p><p>売上は2020暦年・億円（原単位百万円の公表丸め値を合算）。単位未満の値を含む場合は「約」を付けます。小売・飲食サービス・生活関連サービスの3業種で、GDP・付加価値・全産業総売上ではありません。飲食サービスは76・77、生活関連は78・79の対象業種です。小売売場面積は法人小売業の2021年6月1日の値で、オフィス面積ではありません。</p><p>原表の地区別事業所数・従業者数の和が公表総計と一致することを確認しています。これは統計表内の加算関係の確認で、街の境界や地区外も含む網羅性の認定ではありません。</p><p>総務省・経済産業省「令和3年経済センサス‐活動調査 立地環境特性編 第2表」を駅まちアトラスが加工。公表日2024年6月25日。${link(asset.source.url,'公式データ')} ${link(asset.source.definition_url,'集計定義・記号')} ${link(asset.source.terms_url,'利用条件')}</p></details>`;
}
