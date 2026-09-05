# Phase 1 G0/G1 report — 2026-08-30

## 判定

**G0 PASS / G1 PASS（source lock ready）**。

公式カタログ、訂正情報、利用規約、e-Stat更新情報、採用する表定義を取得日に再確認し、
その応答ハッシュを [`official_recheck.phase1.yml`](../data/manifests/official_recheck.phase1.yml)
へ記録した。原本はすべて公式ホストから取得し、CRC・ZIPメンバーのパス安全性・HTTP応答を
検査したうえで、SHA-256を [`source_lock.phase1.yml`](../data/manifests/source_lock.phase1.yml)
へ固定している。

## 取得範囲

| 区分 | 採用入力 | 件数 | 基準時点 | 公表・配布時点 |
|---|---|---:|---|---|
| 鉄道 | N02-25 | 1 | 2025-12-31 | 2026-04カタログ |
| 乗降客 | S12-25（FY2024） | 1 | FY2024 | 2026-04カタログ |
| 地価 | L01-26（埼玉・千葉・東京・神奈川） | 4 | 2026-01-01 | 2026-03-18公表、2026-04-24訂正後 |
| 商業活動 | 経済センサス `T001163`、JGD2011 500m、中分類 | 9 | 2021-06-01 | 2024-09-25公表、2025-10-09都道府県配布 |
| 居住人口 | 国勢調査 `T001141`、JGD2011 500m、人口・世帯 | 9 | 2020-10-01 | 2022-07-27公表、2025-10-09都道府県配布 |

e-Statは都道府県ZIPが最小の取得単位のため、表示4都県（11・12・13・14）に加えて、
10km edge bufferとTX検証を覆う08・09・10・19・22を取得した。隣接県の県全域を
表示集計へ入れることはせず、公式行政界を監査した後にG3.1でscope-awareにclip/rollupする。
都道府県ZIPの同じmesh codeは都道府県成分であり、mesh geometryだけで全値へ一本化しない。範囲の正本は
[`PHASE1_ACQUISITION_SCOPE.yml`](../data/reference/PHASE1_ACQUISITION_SCOPE.yml) である。

## 完全性

- 24 ZIPアーカイブ、合計38,883,077 bytes。
- 91 archive members。全アーカイブで `unzip -t` のCRC検査に成功。
- 絶対パス、`..`、バックスラッシュを含むZIPメンバーはゼロ。
- 最終HTTP応答は全件200。Content-Lengthが提供されたものは実体バイト数と一致。
- N02/S12は公式のUTF-8/Shift-JIS併載を保持。e-Stat `T001163`/`T001141`のテキストはCP932として検出・記録。
- 完全な原本とHTTPヘッダーは `data/raw/phase1/` に置き、読み取り専用化した。rawはGitへ登録しない。
- 取得途中の欠落ZIPはロック対象にせず、`data/raw/phase1/quarantine/failed/` に隔離した。最終ロックは完全な再取得分だけを含む。

## 公式訂正・表定義の再確認

- L01は国土数値情報の2026-04-24訂正（東京都住所）より後のリリースIDを使用し、
  `L01-26_13_GML.zip` のハッシュを固定した。取得時点の訂正ページに、これより後のL01-26訂正掲載はなかった。
- 2020国勢調査の500m JGD2011人口・世帯は `T001141` に固定した。`T001192` は同じ500mでも
  年齢階級表であり、`resident_population` 入力としては除外する。
- 配布開始日（e-Stat 2025-10-09等）は、調査基準日・公表日を置き換えない。
- 欠損・秘匿・合算先・非公表は原表tokenを保持し、0へ変換する処理はまだ存在しない。
- 2026-09-05の追加確認で、[e-Statの提供単位説明](https://www.e-stat.go.jp/pdf/gis/teikyo_mesh_chigai.pdf)は
  都道府県境界をまたぐmeshについて都道府県成分だけを収録すると明記していることを確認した。
  このため、同じmesh codeを重複削除せず、G3.1で行政界に対するscope-aware rollupを行う。

参照した公式ページは [N02カタログ](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N02-2025.html)、
[S12カタログ](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-S12-2024.html)、
[L01カタログ](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-L01-2026.html)、
[訂正情報](https://nlftp.mlit.go.jp/ksj_error.html)、
[e-Stat更新情報](https://www.e-stat.go.jp/help/data-definition-information/update-information)、
[e-Stat利用規約](https://www.e-stat.go.jp/terms-of-use) である。

## 次のゲート

G2で初めてN02を展開し、駅・駅群・ハブ・路線のopaque IDとaliasを構築する。G2では、
同名近接、異名乗換、改称、曖昧な近接をすべてレビューキューへ記録する。現時点では
駅crosswalk、mesh変換、中心地ポリゴン、CoreScale、ランキング、公開UIを生成していない。
