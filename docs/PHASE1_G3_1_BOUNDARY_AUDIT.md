# Phase 1 G3.1 — 行政界ソース監査とscope rollup停止ゲート

**監査日:** 2026-09-05

**結論:** `BLOCKED_PENDING_GSI_USE_DETERMINATION`

**実データ取得・rollup:** 未実行

## 結論

公式行政界候補として国土数値情報 **N03 2026年版** を選定した。これは2026年1月1日時点の全国行政区域面データで、JGD2011のGML・Shape・GeoJSONを提供する。1都3県の外郭、10km解析buffer、そしてTXの5km回廊を地理的に定義する粒度としては適切である。

ただし、N03の個別カタログはCC BY 4.0と明記する一方、原典に国土地理院の数値地図（国土基本情報）・地理院タイルを含み、二次利用には国土地理院への申請等が必要になる場合があると明記している。予定している処理は、行政界をdissolve・buffer・intersectionしてmesh component採否と将来の地図成果に使うものである。これが国土地理院の複製・使用手続のどちらに該当するか、また申請不要かは、このプロジェクトだけでは確定できない。

したがって、N03のraw取得、派生scope polygon、meshのclip/rollup、Core surfaceへの昇格は止める。実装可能なのは、監査記録、将来の計算契約、そして誤って処理を始めないためのvalidatorまでである。

## 公式に確認した事実

| 項目 | 確認結果 | 根拠 |
|---|---|---|
| データ | N03 2026年版、全国の行政区域面 | [N03 カタログ](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N03-2026.html) |
| 基準時点 | 2026-01-01 | [N03 カタログ](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N03-2026.html) |
| 公表/更新 | 2026年4月更新 | [N03 カタログ](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N03-2026.html) |
| 粒度・座標 | 市区町村・行政区等の面、JGD2011（B,L） | [N03 カタログ](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N03-2026.html) |
| 許諾表示 | CC BY 4.0、出典・加工表示が必要 | [N03 カタログ](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N03-2026.html), [国土数値情報利用規約](https://nlftp.mlit.go.jp/ksj/other/agreement.html) |
| 追加条件 | 原典の国土地理院成果について二次利用時に申請等が必要な場合あり | [N03 カタログ](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N03-2026.html) |
| 公式の判定経路 | 国土地理院は、出典表示のみでよい場合と、複製・使用承認が必要な場合を区別する | [国土地理院の利用手続](https://www.gsi.go.jp/LAW/2930-index.html) |

N03には一部暫定境界があること、東京の一部境界・中央防波堤埋立地には修正案内があることもカタログに記載されている。これは中心地の境界には使わず、あくまで解析scopeの外郭とcomponent supportの確定だけに限定する。

## 固定した将来の計算ルール

詳細は [G3.1 boundary audit](../data/reference/G3_1_BOUNDARY_SOURCE_AUDIT.yml) と [scope-rollup contract](../data/reference/G3_1_SCOPE_ROLLUP_CONTRACT.yml) を正本とする。

1. 表示域はN03の都道府県コード接頭辞 `11, 12, 13, 14` をdissolveした面とする。
2. 解析bufferはその面の外側10,000mとする。TX例外はN02の確定した路線形状から作る5,000m回廊だけであり、駅centroidの円または直線接続で代用しない。
3. e-Statの観測supportはfull 500m meshではなく、`full mesh ∩ 当該都道府県N03 polygon` とする。
4. scopeに**全体が入る**都道府県componentだけを加算対象にする。部分的に重なるcomponentは比例配分せず、理由付きで数値合算から除外する。
5. `suppressed`、`not_public`、`aggregation_destination`等を含む集合はCore数値に昇格させない。ゼロは明示的な`observed_zero`だけをゼロとして扱う。
6. 出力名は `scope_mesh_aggregate` とし、scope外の寄与を除いた値を「full mesh値」や「exact trimmed値」と呼ばない。

## 次に必要な外部判断

Ownerが国土地理院の[地図の利用手続](https://www.gsi.go.jp/LAW/2930-index.html)で、次の利用を具体的に判定する必要がある。

- N03-20260101の行政区域ポリゴンを加工して、内部の解析scope・mesh component判定に用いること。
- 加工済みscope geometry、またはそれを使った地図・ベクトル成果を公開する可能性。

申請が必要なら、承認番号・対象成果・配布範囲・表示条件を記録する。申請不要なら、判定根拠と出典/加工表示文言を記録する。どちらも `use_conditions_resolved: true` に更新されるまではN03を取得しない。

## この工程で実行していないこと

- N03 archiveのダウンロードまたはsource lock追加
- N03を読み込むclip/buffer/intersection
- e-Stat componentの全mesh化またはCore candidate surface化
- center抽出、スコア、ランキング、公開UI
