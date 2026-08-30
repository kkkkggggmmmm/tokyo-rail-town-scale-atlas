# Data Dictionary

**Project:** `tokyo-rail-town-scale-atlas`
**Dictionary version:** `0.1.0`
**Status:** Phase 0 canonical candidate

## 1. Canonical grain

公開上の入口は駅だが、規模・類型を計算する正本単位は `center` である。

| Entity | 1行の意味 | Canonical ID | Source keyの扱い |
|---|---|---|---|
| `station` | 1事業者・1路線文脈における物理的な駅地物 | `sta_` + UUIDv7/ULID相当 | N02 station code等はalias |
| `station_group` | 同一駅名・近接ホーム等をまとめた公開上の駅群 | `stg_` + opaque ID | N02 300m group codeは初期候補のみ |
| `hub` | 異名駅も含む、徒歩移動可能な実質的乗換結節点 | `hub_` + opaque ID | 近接だけで自動確定しない |
| `line` | 事業者・路線または分析対象サービス回廊 | `lin_` + opaque ID | N02 route/operator keyはalias |
| `center` | 商業活動が空間的に連続する中心地の恒久identity | `ctr_` + opaque ID | 名称・駅名・座標から生成しない |
| `center_version` | 特定model runで推定した中心地境界と代表点 | `(center_id, model_run_id)` | geometryの変更履歴を保持 |
| `station_center_link` | 駅と中心地の多対多関係 | `scl_` + opaque ID | 自動推定と手動判定を区別 |
| `line_center_link` | 沿線が通過する重複除去済み中心地 | `lcl_` + opaque ID | 同じ中心地を複数駅分数えない |

### ID不変条件

1. IDは名称、緯度経度、順序、N02コードから再計算しない。
2. 外部キーは `entity_alias` に `source_release_id` と有効期間付きで保存する。
3. 改称・軽微な位置補正・境界更新では同じIDを保つ。
4. 中心地の分割・統合は新しいIDを発行し、`center_lineage` に関係を残す。
5. ID候補の衝突・多対多曖昧性は `identity_review_queue` に止め、推測で解決しない。

## 2. Null / zero contract

数値列の `NULL` は「値が0」ではなく、「数値として利用できない」を意味する。
`observation_status` と `raw_value` が必須の意味情報である。

| Status | 意味 | `numeric_value` | Core集計 |
|---|---|---:|---|
| `observed` | 正の公表観測値 | required | 可 |
| `observed_zero` | 公表された真の0 | `0` | 可 |
| `imputed` | 出典または明示手法による補完 | nullable | 原則別系列 |
| `suppressed` | 秘匿 | `NULL` | 不可 |
| `aggregation_destination` | 秘匿値の合算先 | source value | 重複制御必須 |
| `not_public` | 非公表 | `NULL` | 不可 |
| `not_surveyed` | 未調査 | `NULL` | 不可 |
| `not_applicable` | 該当なし | `NULL` | 0へ変換不可 |
| `source_absent` | 出典に値・行・点がない | `NULL` | 不可 |
| `duplicate_on_other_record` | 別レコードへ掲載 | `NULL` | 掲載先のみ利用 |
| `station_absent` | 当該時点に駅なし | `NULL` | 不可 |
| `outside_scope` | 対象範囲外 | `NULL` | 不可 |
| `invalid` | 型・単位・codeが不正 | `NULL` | pipeline fail |

未認識tokenは `invalid` として処理を停止する。空欄、`X`、`...`、`-` を
一律に0へ変換してはならない。

## 3. Time contract

全観測に次を独立して持たせる。

| Field | 定義 |
|---|---|
| `reference_start` / `reference_end` | 統計・地物が表す時点または期間 |
| `survey_date` | 調査基準日。単日でない場合はNULLと注記 |
| `published_at` | 提供主体が公表した時点 |
| `retrieved_at` | 本プロジェクトが実体を取得した時点 |
| `source_release_id` | 取得した版・訂正版を一意に示すID |

例: 2021経済センサス、2020国勢調査、FY2024乗降客、2025-12-31鉄道、
2026-01-01地価をまとめて「2026年値」と表示しない。

## 4. Canonical table fields

### `station`

| Field | Type | Nullable | Definition |
|---|---|---:|---|
| `station_id` | text | no | 不変の内部ID |
| `display_name_ja` | text | no | 現行表示名。identityには使わない |
| `operator_id` | text | yes | canonical operator。Phase 1で確定 |
| `station_kind` | enum | no | `surface`, `underground`, `mixed`, `unknown` |
| `lifecycle_status` | enum | no | `active`, `closed`, `planned`, `unknown` |
| `valid_from`, `valid_to` | date | yes | 実体としての有効期間 |
| `centroid_wkb` | geometry | yes | 便宜的代表点。駅境界そのものではない |
| `geometry_crs` | text | yes | 原則 `EPSG:6668` |

### `station_group`

| Field | Type | Nullable | Definition |
|---|---|---:|---|
| `station_group_id` | text | no | 内部ID |
| `display_name_ja` | text | no | 公開表示名 |
| `group_rule` | enum | no | `source_seed`, `same_facility`, `manual_adjudication` |
| `review_status` | enum | no | `candidate`, `confirmed`, `rejected`, `deprecated` |

`station_group_member` が駅群の構成員と根拠を保持する。N02の同名300mグループは
`source_seed` であり、確定判定ではない。

### `hub`

| Field | Type | Nullable | Definition |
|---|---|---:|---|
| `hub_id` | text | no | 内部ID |
| `display_name_ja` | text | no | 結節点の表示名 |
| `transfer_basis` | enum | no | `official`, `paid_area`, `signed_walk`, `manual` |
| `review_status` | enum | no | `candidate`, `confirmed`, `rejected`, `deprecated` |

`hub_station_group_link` は駅群とhubの多対多関係を持つ。単なる300m以内は
`transfer_basis` にならない。

### `center` / `center_version`

| Field | Type | Nullable | Definition |
|---|---|---:|---|
| `center_id` | text | no | 中心地identity |
| `display_name_ja` | text | no | 暫定名称。名称変更でIDを変えない |
| `parent_center_id` | text | yes | 巨大中心地とsubareaの階層 |
| `center_level` | enum | no | `parent`, `center`, `subarea` |
| `identity_status` | enum | no | `candidate`, `confirmed`, `retired` |
| `model_run_id` | text | no | 境界を生成した実行 |
| `polygon_wkb` | geometry | yes | 固定半径でない推定境界 |
| `geometry_crs` | text | no | 原則メートル系計算CRSを記録 |
| `boundary_method` | text | no | アルゴリズムとparameter set |
| `boundary_confidence` | decimal | yes | 0–1。未計算はNULL |
| `manual_override_id` | text | yes | 修正がある場合の根拠 |

### `station_center_link`

| Field | Type | Nullable | Definition |
|---|---|---:|---|
| `station_center_link_id` | text | no | link ID |
| `station_group_id` | text | no | 公開入口としての駅群 |
| `center_id` | text | no | 関連中心地 |
| `model_run_id` | text | no | 判定版 |
| `role` | enum | no | `core`, `auxiliary`, `edge`, `transfer_only`, `multi_entry` |
| `link_confidence` | decimal | yes | 0–1 |
| `evidence_json` | json | no | 距離、包含、ネットワーク、監査根拠 |
| `is_manual` | boolean | no | 手動overrideか |

一駅から複数中心地へのリンクを許す。`transfer_only` は中心地規模へ寄与させない。

### `line_center_link`

| Field | Type | Nullable | Definition |
|---|---|---:|---|
| `line_center_link_id` | text | no | link ID |
| `line_id` | text | no | 分析路線・回廊 |
| `center_id` | text | no | 通過中心地 |
| `model_run_id` | text | no | 算定版 |
| `first_sequence`, `last_sequence` | integer | yes | 同一中心地に属する駅順の範囲 |
| `linked_station_group_count` | integer | no | 関係駅数。中心地数には使わない |
| `distance_along_line_km` | decimal | yes | 代表位置 |

`UNIQUE(line_id, center_id, model_run_id)` により、同じ街を複数駅として沿線集計しない。

### `feature_observation`

| Field | Type | Nullable | Definition |
|---|---|---:|---|
| `observation_id` | text | no | 観測ID |
| `entity_type`, `entity_id` | text | no | station/group/hub/center/grid/land point等 |
| `metric_code` | text | no | 単位と定義を固定した指標コード |
| `numeric_value` | decimal | yes | 正規化済み数値。欠損時NULL |
| `raw_value` | text | yes | 原表tokenをそのまま保存 |
| `observation_status` | enum | no | Null / zero contractのstatus |
| `unit` | text | no | persons, establishments, yen_per_m2等 |
| `source_release_id` | text | no | 版・訂正版 |
| `source_record_key` | text | no | 原表へ戻れるkey |
| `reference_start`, `reference_end` | date | yes | 対象時点・期間 |
| `published_at`, `retrieved_at` | timestamp | yes/no | 公表・取得時点 |

## 5. Core feature codes

| Metric code | Unit | Primary source | Domain | Notes |
|---|---|---|---|---|
| `retail_establishments` | establishments | 2021 Economic Census mesh | Scale/Type | 中分類を優先 |
| `retail_employees` | persons | same | Scale | Activity Mass主成分候補 |
| `food_establishments` | establishments | same | Scale/Type | 飲食と宿泊の分離可否を原表で確認 |
| `food_employees` | persons | same | Scale/Type | 同上 |
| `lifestyle_leisure_establishments` | establishments | same | Scale/Type | 分類定義をversion固定 |
| `lifestyle_leisure_employees` | persons | same | Scale/Type | 分類定義をversion固定 |
| `all_industry_employees` | persons | same | Type/context | 業務性補助。商業量へ無条件加算しない |
| `resident_population` | persons | 2020 Census mesh | Type/context | 商業量ではない |
| `daily_ridership` | persons/day | S12 | Access | CoreScaleへ混入禁止 |
| `commercial_land_price` | yen/m² | L01 | Validation | point sample。CoreScaleへ混入禁止 |

## 6. Score outputs

Phase 0では値を生成しない。将来の出力は別列・別版で保持する。

| Output | Meaning | Must not include |
|---|---|---|
| `core_scale` | 活動総量・広がり・密度 | 乗降客、地価、地域差の大きいPOI |
| `access_power` | 乗降客・路線数・結節性 | 商業規模への直接加算 |
| `center_type` | 規模を除いた構成特徴 | CoreScaleそのもの |
| `confidence` | freshness・coverage・boundary stability | 規模・人気の代理 |
| `transport_town_gap` | Access percentile − CoreScale percentile | raw score同士の無単位減算 |

詳細なDDLは [`schema/canonical.sql`](schema/canonical.sql) を正本とする。
