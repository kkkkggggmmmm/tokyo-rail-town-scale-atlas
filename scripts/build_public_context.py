#!/usr/bin/env python3
"""Build public context and a reproducible SVG from approved reference records."""
from pathlib import Path
import json
import subprocess
from html import escape
ROOT=Path(__file__).resolve().parents[1]
def main():
    economy=json.loads((ROOT/'data/reference/quantitative/municipal_economy.json').read_text())
    education=json.loads((ROOT/'data/reference/quantitative/education_safety.json').read_text())
    records=[]
    for item in economy['items']:
        assert item['approved_for_public_display']
        source=economy['sources'][item['source_id']]
        records.append({**item,'geographyLabel':item['scope_label'],'metricLabel':item['metric_label'],
            'periodLabel':item.get('reference_period',item.get('reference_date')),'sourceUrl':source['url'],
            'displayNote':' '.join([item['interpretation'],item.get('scope_note','')]).strip(),
            'license':source['license_id'],'attribution':source['attribution'],'termsUrl':source['terms_url']})
    context={'version':'0.3','economy':{'records':records,'sources':economy['sources']},'educationSafety':education}
    (ROOT/'dist/context.json').write_text(json.dumps(context,ensure_ascii=False,separators=(',',':'))+'\n')
    js="import {readFileSync} from 'node:fs';import {evaluateRoutes} from './dist/app.mjs';console.log(JSON.stringify(evaluateRoutes(JSON.parse(readFileSync('./dist/data.json')))));"
    rows=json.loads(subprocess.check_output(['node','--input-type=module','-e',js],cwd=ROOT,text=True))
    keys=['restaurants','retail','employees'];labels=['飲食店','小売事業所','全産業従業者'];units=['店','事業所','人']
    maxima={k:max(r['metrics'][k]['median'] or 0 for r in rows) or 1 for k in keys}
    def text(x,y,t,size=15,color='#274338',weight='400'):
        return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}">{escape(str(t))}</text>'
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1500" viewBox="0 0 1200 1500" role="img" aria-labelledby="title desc">',
        '<title id="title">東京圏8沿線・駅所在区画の商業と就業</title><desc id="desc">2021年経済センサス。駅を含む500m区画の都県別公表分の中央値。複数都県の区画と秘匿値を除外。8沿線の3指標を同じ縮尺で比較する。</desc>',
        '<rect width="1200" height="1500" fill="#f4f6ef"/><g font-family="Noto Sans JP, sans-serif">',
        text(50,57,'駅まちアトラス  /  DATA COMPARISON',14,'#617465'),text(50,106,'沿線を、実数で比べる。',36,weight='700'),
        text(50,140,'駅を含む約500m区画・都県公表分の中央値 ｜ 2021年経済センサス',16),
        text(50,170,'同じ区画は沿線内で1回。繁華街全体の合計・駅から500m圏の集計ではありません。',14,'#617465')]
    for i,r in enumerate(rows):
        x=50+(i%2)*560;y=200+(i//2)*275;color=r.get('color','#367963')
        svg.append(f'<rect x="{x}" y="{y}" width="540" height="253" rx="12" fill="white" stroke="#d9e2d8"/><rect x="{x}" y="{y}" width="540" height="5" fill="{color}"/>')
        svg.extend([text(x+20,y+38,r['name'],22,weight='650'),text(x+20,y+65,f"{r['start']} — {r['end']}  /  {r['stationCount']}駅レコード・{r['meshCount']}区画",13,'#617465')])
        for j,k in enumerate(keys):
            m=r['metrics'][k];v=m['median'];yy=y+96+j*43;number='—' if v is None else f'{v:,.1f}'.removesuffix('.0')
            svg.extend([text(x+20,yy,labels[j],13),text(x+265,yy,f'{number} {units[j]}  [{m["count"]}/{m["total"]}区画]',13),f'<rect x="{x+20}" y="{yy+9}" width="500" height="6" rx="3" fill="#e8eee5"/><rect x="{x+20}" y="{yy+9}" width="{500*(v or 0)/maxima[k]:.3f}" height="6" rx="3" fill="{color}"/>'])
        avg='算定保留' if r['meanRank'] is None else f'{r["meanRank"]:.1f}位'
        svg.append(text(x+20,y+229,f'3指標の平均順位：{avg} / 8沿線（小さいほど中央値が高い）',12,'#617465'))
    svg.extend([text(50,1340,'出典：総務省・経済産業省「令和3年経済センサス」地域メッシュ統計。駅まちアトラスが加工。',13),
        text(50,1366,'平均順位 = 飲食店・小売・従業者の中央値による8沿線内順位の平均（同値は同順位）。',13,'#617465'),
        text(50,1392,'各指標の取得率90%以上で算定。教育・治安・売上・床面積・駅利用人数は含みません。',13,'#617465'),
        text(50,1418,'区画・駅の位置、欠損、対象区間に影響される参考比較です。CoreScale・住みやすさ順位ではありません。',13,'#617465'),
        '<a href="https://tokyo-rail-town-atlas.dwdaai.chatgpt.site">'+text(50,1464,'tokyo-rail-town-atlas.dwdaai.chatgpt.site  ｜  v0.3 ・ 2026-09-08',14)+'</a></g></svg>'])
    (ROOT/'dist/route-comparison.svg').write_text('\n'.join(svg)+'\n')
    print(f'PASS context: {len(records)} economic records, {len(education["crime"]["records"])} crime records, {len(education["cramSchools"]["records"])} school locations; SVG {len(rows)} routes')
if __name__=='__main__':main()
