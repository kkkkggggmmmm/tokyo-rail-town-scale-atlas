# Data Dictionary

**Project:** `tokyo-rail-town-scale-atlas`
**Dictionary version:** `0.5.0`
**Status:** Phase 1 G3 normalization PASS; G3.1 scope-rollup contract fixed but N03 use determination pending (not publication-ready)

## 1. Canonical grain

公開上の入口は駅だが、規模・類型を計算する正本単位は `center` である。

| Entity | 1行の意味 | Canonical ID | Source keyの扱い |
|---|---|---|---|
| `station` | 1事業者・1路線文脈における物理的な駅地物 | `sta_` + persisted opaque registry value | N02 station code等はalias |
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
| `resident_population` | persons | 2020 Census mesh, e-Stat `T001141` (JGD2011 500m) | Type/context | 商業量ではない。`T001192` age-class table is not this input |
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

## 7. Phase 1 G2 confirmed identity artifacts

G2では、ロック済みN02-25から8つのpilot回廊を切り出し、12件の手動判定と
exact service segment監査を通過した。判定の正本は
`data/reference/PHASE1_G2_ADJUDICATIONS.yml`、再生成結果のハッシュは
`data/manifests/identity.phase1.yml` に保持する。この確定はG3入力としてのidentityを
意味し、中心地・スコア・ランキングの公開を許可するものではない。

| Artifact | Grain | Key rule |
|---|---|---|
| `data/derived/stations.parquet` | confirmed N02 source station node | `station_id` is a persisted opaque registry ID; N02 key is alias |
| `data/derived/station_groups.parquet` | reviewed N02 `N02_005g` seed | `confirmed` records passed collision/hub review; the source seed alone remains insufficient evidence |
| `data/derived/hubs.parquet` | confirmed operational transfer hub | 10 rows use `transfer_basis=official`; a multi-group hub has nullable legacy single-group columns |
| `data/derived/hub_station_group_links.parquet` | hub × station group | authoritative many-to-many membership with manual-adjudication evidence |
| `data/derived/lines.parquet` | frozen pilot analysis corridor | all 8 rows are `confirmed_exact_segment` with station-order and source-key SHA-256 locks |
| `data/derived/station_line_crosswalk.parquet` | station × pilot line membership | 233 confirmed primary memberships; exact segment order is contiguous |
| `data/derived/entity_alias.parquet` | canonical entity × source/adjudication alias | dated `source_release_id` and review status are mandatory |
| `data/qa/identity_review_queue.parquet` | identity review history | 13 resolved rows, including the 12 formerly open hub cases; no history is deleted |

`distance_from_origin_km` in the G2 crosswalk remains a geodesic centroid-chain candidate,
not an operating-kilometre claim. Exact segment confirmation fixes membership and order,
not sales-distance semantics. `lines.parquet` stores `segment_station_order_sha256`,
`segment_source_keys_sha256`, `segment_lock_version`, and `segment_evidence_json`.
The source rule and persisted ID registry are `data/reference/PHASE1_IDENTITY_RULES.yml`
and `data/reference/PHASE1_IDENTITY_REGISTRY.yml`.

The G2 Parquet stores `centroid_lon` / `centroid_lat` for lightweight review;
the canonical SQL `centroid_wkb` field remains the geometry interchange target for a
later promoted run.

## 8. Phase 1 G3 local normalization artifacts

G3 output is a reproducible local derivative, not a Git-tracked publication dataset and
not a canonical `center` result. Its detailed run record is
`docs/PHASE1_G3_NORMALIZATION_REPORT.md`; `make verify-g3` validates a locally regenerated
run.

| Artifact | Grain | Primary key | Important constraint |
|---|---|---|---|
| `economic_mesh_500m.parquet` | economic-census prefecture component × 500m mesh | `mesh_partition_observation_id` | `mesh_code` alone is deliberately non-unique at prefecture borders. |
| `population_mesh_500m.parquet` | census prefecture component × 500m mesh | `mesh_partition_observation_id` | `HTKSYORI` controls suppression / aggregate-destination semantics. |
| `station_access_observations.parquet` | confirmed station-line membership × S12 source feature | `(station_line_key, source_record_key)` | `allowed_score_domain=access`; it cannot feed `core_scale`. |
| `land_price_points.parquet` | L01 standard-land point | `land_point_source_key` | `allowed_score_domain=validation`; it cannot feed `core_scale`. |

### G3 common provenance and partition fields

| Field | Meaning |
|---|---|
| `source_raw_record_key` | 原表に書かれたmesh code。県境では単独で一意ではない。 |
| `source_record_key` | source family、都道府県成分、mesh codeを含む派生時の一意key。 |
| `mesh_partition_observation_id` | `source family:prefecture partition:mesh code`。G3のmesh観測主キー。 |
| `prefecture_partition_code` | e-Stat都道府県配布における寄与成分の都道府県コード。 |
| `mesh_partition_count` / `mesh_partition_codes_json` | 取得範囲で同一mesh codeを持つ都道府県成分数と一覧。 |
| `cross_partition_rollup_status` | `single_prefecture_component` または `requires_scope_aware_prefecture_component_sum`。 |
| `partition_geometry_status` | G3ではfull 500m meshであり、都道府県境界clip済みと主張しない。 |
| `<metric>_raw`, `<metric>_value`, `<metric>_status` | 原表token、正規化数値、観測状態の三組。空白・秘匿・非公開・duplicateを0にしない。 |
| `source_reference_period`, `source_published_at`, `raw_recovered_at` | 調査基準時点、公表時点、今回のraw復旧時点。互いに置換しない。 |

都道府県meshの同一`mesh_code`は、e-Statの提供仕様上、各都道府県の寄与分である。
全mesh値へ合算するには、公式行政界に対する表示域・10km buffer・TX例外のclipを先に
監査する必要がある。したがってG3の`analysis_eligible`は成分の取得範囲フラグであって、
full mesh surfaceへの採用許可ではない。

## 9. G3.1 scope-aware rollup contract (not yet executable)

`data/reference/G3_1_SCOPE_ROLLUP_CONTRACT.yml` は、N03の利用条件が公式に確定した後だけ
実行できる将来のrollup仕様である。現時点ではN03 archiveや派生geometryを保持しない。

| Field / rule | Meaning |
|---|---|
| `component_support` | `full mesh polygon ∩ matching prefecture N03 polygon`。full meshを都道府県成分のgeometryと偽称しない。 |
| `scope_mesh_aggregate` | 承認済みscope内に完全に入るcomponentだけの合計。scope外の寄与を除くのでfull mesh値とは呼ばない。 |
| `excluded_partial_component_ids_json` | scopeに一部だけ重なるcomponent。面積比で数値を配分せず、理由付きで保存する。 |
| `scope_mesh_aggregate_status` | 全included componentが`observed`または`observed_zero`のときだけ数値合計可。秘匿・未公表・aggregation destinationはCore不可。 |
| TX geometry | N02路線geometryによる5km回廊。station centroidの円や直線接続は不可。 |

N03のカタログはCC BY 4.0を表示するが、国土地理院原典の二次利用手続が必要となる場合を
明記している。`G3_1_BOUNDARY_SOURCE_AUDIT.yml` の`use_conditions_resolved`が`true`になるまで、
この節はデータ処理の権限ではなく停止条件である。

## 10. 公開定量地図 v0.3（2026-09-08追加）

|公開フィールド|単位・範囲・意味|
|---|---|
|`stations[].id` / `groupId`|確定済みG2 station/station_group IDを引き継ぐ。駅名から新規生成しない。|
|`coordinates`|N02代表座標、`coordinateCRS`を保持。図上の任意配置ではない。|
|`officialRouteCount`|N02同一駅群内の事業者・正式路線ペアのdistinct数。運転系統数ではない。|
|`ridership.value`|S12 FY2024人/日。単一の非重複観測が確定する場合のみ。事業者・路線間の合計禁止。|
|`meshContexts[code].economicComponents`|都県別公表成分を個別保持。`fullMeshRollup:false`。|
|`restaurants`|T001163082、76飲食店の事業所数。080（宿泊業・飲食サービス業全体）とは異なる。|
|`retail`|T001163062、小売業事業所数。|
|`employees`|T001163108、全産業従業者数。オフィス従業者・床面積ではない。|
|`populationComponents`|2020年人口。合算元/先・処理コードを保持し、合算値を単一区画人口としない。|
|`route_station_context_mean_rank_v1`|沿線の駅所在区画の飲食・小売・就業中央値を8沿線内で順位付けし、1/3ずつ平均。取得率90%以上。CoreScaleとは別の参考比較。|
|`context.economy` / `educationSafety`|自治体・町・個別校舎という資料の範囲を保持。駅域に割り付けず、沿線指数へ混入しない。|

全数値は値・単位・調査時点・地域範囲・出典の組で表示する。中学受験率の欠損はnull。私立国立中学への進学率と同義にしない。

## 11. 公開追加指標 v0.4（2026-09-08）

|公開フィールド|単位・範囲・意味|
|---|---|
|`economicComponents[].apparel`|T001163064、2021年6月1日・500m区画の都県公表分。産業57「織物・衣服・身の回り品小売業」の事業所数。衣服、靴、服飾品等を含み、アパレルブランド店舗だけの数ではない。|
|`students.meshContexts[code].components[].university`|T001144046、2020年10月1日・大学大学院在学者の居住人数。大学への流入学生数や駅利用学生数ではない。|
|`juniorCollege` / `highSchool` / `allStudents`|T001144043/040/034。同日の短大高専、高校、全在学者の居住人数。全在学者を大学生数と呼ばない。|
|`studentShare`（画面・CSVで算出）|在学者居住人数÷同一日・同一mesh・同一都県の総人口×100。双方通常処理・公表数値・単一都県成分・分母>0のときのみ。秘匿/合算先/県境の比率はnull。|
|`commercial-districts.districts[].source_district_id`|公式表2の8桁商業集積地区コード。原資料のIDであり canonical center IDではない。名称で駅と自動結合しない。|
|`retail_sales_million_yen` / `food_service_sales_million_yen` / `personal_service_sales_million_yen`|2020暦年の売上（収入）、原単位百万円。画面は100で割った億円。小売I2、飲食M2（76+77）、生活関連Nの対象業種。GDPや全産業総売上ではない。|
|`three_sector_sales_million_yen`|3業種すべての売上が数値公表される場合の和。秘匿・該当数字なしを0補完しない。沿線合計へ加算しない。|
|`below_rounding_unit`|売上原表の0は百万円未満。「単位未満」と表示し、含まれる合計には「約」。実際の売上0と断定しない。|
|`retail_sales_floor_sqm`|2021年6月1日の法人小売業売場面積㎡。事務所・オフィス面積ではない。|
|`cafes.observations[].value`|2021年6月1日、産業小分類767・うち民営・全従業者規模。自治体/政令市区全体の喫茶店事業所数。駅圏の数ではない。|
|`cafes[].symbol_unresolved`|非数値記号の6地域は原文+nullで保持、公開数値一覧から除外。親市と区の合算禁止。|

出典は `data/manifests/public_supplements.yml` と各公開JSONに保持。調査時点・公表日・取得日は別項目。T001144の表固有公表日は未確認としてnull、シリーズ公表日や配布年月で代用しない。追加4指標は既存の飲食・小売・就業3指標平均順位へ混入しない。学生居住割合は教育水準や大学への通学流入を意味しない。


## 12. エリア別公表地区合計 v0.10（2026-09-12）

|フィールド・規則|意味|
|---|---|
|`AREA_SUM_METHOD.version`|`selected-district-sum-v1`。集計対象は原表の地区集合で、街全域の地理的網羅性は未認定。|
|`DISTRICT_AREAS[].sourceDistrictIds`|固定8エリアの合計対象となる全44公表地区ID。元の地区名称と数値を内訳表示。自治体・都県総計は混ぜない。|
|`selectedDistrictSumAllowed` / `aggregationAllowed`|前者trueは公表地区集合の加算、後者falseは未認定のcanonical center／地理的な街全域集計を引き続き禁止。|
|`aggregateArea.metrics[key].value`|全対象地区の同指標が数値公表される場合だけその和。売上は百万円、画面は÷100の億円。3業種計は地区×3項目すべてが必要。|
|`complete` / `observed` / `expected`|完全な合計か、公表値の数、必要な値の数。3業種計以外は地区数、3業種計は地区×3項目数。範囲外の店舗を含む網羅率ではない。|
|`missing`|欠けた地区ID・地区名・指標・元のstatusを保持。原表の秘匿・該当数字なし・未取得はいずれもnull、0補完しない。|
|`rounded`|単位未満の公表値を含む合計には「約」を付ける。すべての売上は原表の丸め精度で加算。|
|`identityValid`|各地区IDが原表に一意にあり、リスト内重複がない。`rankAreas`は全エリアの重複所属も検知して該当エリアを集計不可にする。|
|`rank`|選択条件内の同一指標・年度で順位（同値1,1,3）。不完全な合計はnullで常に末尾。原表の施設単位等とは混ぜない。|
|検索・都県条件|エリアを選ぶ条件。地区名で検索してもエリア内の加算対象は削らない。|

加算可能性の確認はDEC-0016の原表総計との照合に基づく。各エリア名は明示された地区集合を指す。
地理的な街全域、地区外も含む店舗総数、全産業売上、GDPの算定を意味しない。


### v0.11 拡張（2026-09-13）

`AREA_SUM_METHOD.version = selected-district-sum-v2`。固定26エリア・200公表地区へ拡張。
東京都16／神奈川県3／埼玉県3／千葉県4。v1の8エリアのID・対象地区・合計値を保持する。
数値がすべてそろう合計は小売23、飲食19、生活12、3業種計11、売場22エリア。
集計・欠損・順位規則は変更しない。各エリアの `scopeNote` に対象外の地区や未確認の帰属も明示する。
26エリアは東京圏の全地域ではなく、公表地区集合に基づく先行比較対象である。
