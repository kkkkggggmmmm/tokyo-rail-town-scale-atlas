# 公式配布・訂正再確認 — 2026-09-05

## 判定

**PASS（現行カタログ・利用条件・既存source lockとのbyte一致を再確認）**。ただし、
現行の国土数値情報訂正ページをテキスト検索した結果だけから「それ以後の訂正が存在しない」
とは断定しない。この限定は記録上の不確実性であり、L01-26を未訂正値へ戻す理由にはならない。

今回のraw recoveryでは、固定済みの24 ZIPを公式URLから再取得し、
`make verify-locked` で既存の24 archive / 91 member のbyte lockに一致した。
source lockの再作成や、raw値・基準時点・公表時点の書換えは行っていない。

## 再確認結果

| 入力 | 現在確認できた公式事実 | 今回の判断 |
|---|---|---|
| N02-25 | [2025年鉄道カタログ](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N02-2025.html) は基準日を2025-12-31、利用条件をCC BY 4.0として継続掲載している。今回のarchive HEAD応答は既存lockの14,903,774 bytes・ETagと一致した。 | N02-25をG2/G3入力として継続。canonical station IDは依然としてN02コードではない。 |
| S12-25 / FY2024 | [駅別乗降客数カタログ](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-S12-2024.html) は、非公表駅と元データの時間差を明記している。 | `S12_058` duplicate、`S12_059` existenceを数値より先に解釈し、Access以外へ流用しない。 |
| 経済センサス `T001163` | [更新情報](https://www.e-stat.go.jp/help/data-definition-information/update-information) はJGD2011 500mの配布イベントを継続記載し、[定義PDF](https://www.e-stat.go.jp/help/data-definition-information/downloaddata/T001163.pdf) に採用中分類列を示す。 | 2021-06-01を基準時点として維持し、2025年の配布日は観測時点に置換しない。 |
| 国勢調査 `T001141` | [更新情報](https://www.e-stat.go.jp/help/data-definition-information/update-information) と[定義PDF](https://www.e-stat.go.jp/help/data-definition-information/downloaddata/T001141.pdf) により、JGD2011 500m人口・世帯表として確認した。 | `T001141`を維持し、年齢階級表`T001192`を`resident_population`へ混入させない。 |
| L01-26 | [2026年地価公示カタログ](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-L01-2026.html) は基準日2026-01-01を継続掲載する。2026-04-24の東京住所訂正後に固定した`L01-26_13_GML.zip`は、再取得後も既存SHA-256 lockと一致した。 | L01は検証レイヤーのまま維持する。今回の可視テキスト検索では、訂正ログにおける過去コードの完全な不在までは証明していないため、将来の再取得時には訂正ページとbytesを再監査する。 |

利用条件は、国土数値情報の[利用約款](https://nlftp.mlit.go.jp/ksj/other/agreement_01.html)と
e-Statの[利用規約](https://www.e-stat.go.jp/terms-of-use)を再確認した。いずれも本プロジェクトの
出典表示・改変明示・raw provenance保持の契約と矛盾しない。

## 判断を変えた公式事実：都道府県メッシュは「重複」ではない

e-Statの[第1次地域区画と都道府県の違い](https://www.e-stat.go.jp/pdf/gis/teikyo_mesh_chigai.pdf)は、
都道府県単位のダウンロードでは、都道府県境界をまたぐ同一メッシュについて当該都道府県分だけを
収録し、隣接都道府県分を足し上げないと明記している。これは人口だけでなく経済センサスの
事業所数等にも同様に適用される。

したがって、今回見つかった同じ`mesh_code`の複数行は、削除すべき重複ではない。G3は
`(source family, prefecture partition, mesh_code)`を観測IDとして保存し、公式行政界による
scope clipが確定するまで全メッシュの合算・density surface化を行わない。この判断は
[G3正規化報告](PHASE1_G3_NORMALIZATION_REPORT.md)とDEC-0014に固定する。

## この再確認が証明しないこと

1. 現行訂正ページの検索可能テキストだけで、未表示・将来掲載を含む訂正の不存在を証明すること。
2. 行政界10km bufferの正確なポリゴンclip。
3. 500mメッシュを街路・建物・出入口単位に細分すること。

これらは推測で補わない。次の入力ゲートは、利用条件と時点を監査した公式行政界データを
導入し、都道府県成分のscope-aware rollupを明示的に検証することである。
