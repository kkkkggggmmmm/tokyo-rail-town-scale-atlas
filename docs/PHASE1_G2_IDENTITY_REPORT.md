# Phase 1 G2 identity report — 2026-08-31

## 判定

**PASS — G2を閉じ、G3へ進める。** 2026-08-30のcanonical `main`（`0607003`）に残っていた12件を、現行の事業者公式情報とロック済みN02-25により全件判定した。8回廊のexact service segmentも駅順とsource-key列のSHA-256付きで固定した。

N02の同名300m group seedや近接だけではhubを確定していない。各confirm/rejectは `data/reference/PHASE1_G2_ADJUDICATIONS.yml` の公式根拠に従い、履歴行は削除せずreview queueで `resolved` とした。

## 件数

- pilot回廊: 8
- confirmed station node: 242
- confirmed station_group: 231
- confirmed hub: 10
- confirmed station-line crosswalk: 233
- identity review queue: 13（open 0 / resolved 13）

## 12件の判定

| source key | 表示 | 判定 |
|---|---|---|
| `003505` | 上野 | hub確定 |
| `003615` | 御茶ノ水 | hub確定 |
| `003624` | 秋葉原 | hub確定 |
| `003677` | 神田 | hub確定 |
| `003700` | 新宿 | hub確定 |
| `003872` | 新橋 | hub確定 |
| `003922` | 渋谷 | hub確定 |
| `004387` | 町田 | hub確定 |
| `004633` | 横浜 | hub確定 |
| `manual:asakadai-kitaasaka` | 朝霞台—北朝霞 | hub確定 |
| `manual:asakusa-ginza-tx` | 浅草（銀座線—TX） | hub不成立（分離維持） |
| `manual:machida-jr-odakyu` | 町田（JR—小田急） | 既存hubへ重複統合 |

結果は既存9 hubを確定、朝霞台—北朝霞を2 station_groupからなるhubとして追加、浅草（銀座線—TX）は公式乗換の相互記載がないため分離維持、町田の手動候補は既存 `004387` hubへの重複として解消した。

## Exact service segments

| corridor | endpoints | stations | status |
|---|---|---:|---|
| `pc_jr_chuo_rapid` | 東京—高尾 | 24 | `confirmed_exact_segment` |
| `pc_jr_sobu_local` | 御茶ノ水—千葉 | 21 | `confirmed_exact_segment` |
| `pc_jr_keihin_tohoku_negishi` | 大宮—大船 | 42 | `confirmed_exact_segment` |
| `pc_tokyu_toyoko` | 渋谷—横浜 | 21 | `confirmed_exact_segment` |
| `pc_odakyu_odawara` | 新宿—小田原 | 47 | `confirmed_exact_segment` |
| `pc_tobu_tojo` | 池袋—寄居 | 39 | `confirmed_exact_segment` |
| `pc_tokyo_metro_ginza` | 渋谷—浅草 | 19 | `confirmed_exact_segment` |
| `pc_tsukuba_express` | 秋葉原—つくば | 20 | `confirmed_exact_segment` |

中央快速線は候補20駅をそのまま承認せず、公式の東京—高尾24駅へ修正した。高円寺・阿佐ヶ谷・荻窪・西荻窪をprimaryへ移し、中央・総武緩行だけの8駅は `auxiliary_context` に残した。京浜東北・根岸線は3つのN02 physical route aliasを跨ぐ大宮—大船42駅のservice corridorとして固定した。

東武東上線は現行の公式路線別ページが駅名付きで列挙する39駅を採用した。同社会社概要の集計値40との定義差はadjudicationに残し、駅ノード選択には直接列挙を優先した。

## 成果物

- `data/reference/PHASE1_G2_ADJUDICATIONS.yml`
- `data/derived/stations.parquet`
- `data/derived/station_groups.parquet`
- `data/derived/hubs.parquet`
- `data/derived/hub_station_group_links.parquet`
- `data/derived/lines.parquet`
- `data/derived/station_line_crosswalk.parquet`
- `data/derived/entity_alias.parquet`
- `data/qa/identity_review_queue.parquet`
- `data/manifests/identity.phase1.yml`

## G3 handoff

G3はこのconfirmed crosswalkを入力としてmesh table・公式mesh geometry・S12 code・L01 pointを正規化できる。中心地、スコア、ランキング、公開UIは引き続き生成しておらず、publication gateは閉じたまま。

参照: `data/reference/PHASE1_G2_ADJUDICATIONS.yml`, `data/reference/PHASE1_IDENTITY_RULES.yml`, `data/reference/PHASE1_IDENTITY_REGISTRY.yml`, `data/manifests/source_lock.phase1.yml`
