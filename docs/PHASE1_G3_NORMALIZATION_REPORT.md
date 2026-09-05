# Phase 1 G3 正規化報告 — 2026-09-05

## 判定

**NORMALIZATION PASS WITH SCOPE GATES PENDING**。

G3は、固定済みraw sourceを、欠損・秘匿・重複・基準時点を失わないローカル派生物へ
正規化した。中心地候補、CoreScale、ランキング、最終中心地ポリゴン、公開UIは作成していない。

最終状態は`NORMALIZATION_PASS_WITH_SCOPE_AWARE_MESH_ROLLUP_AND_BOUNDARY_CLIP_PENDING`である。
これは正規化の失敗ではなく、未監査の行政界で県境メッシュを近似的に合算しないための
意図的な停止点である。

## 実行・検証結果

| チェック | 結果 |
|---|---|
| `make verify-fast PYTHON=.venv/bin/python` | PASS |
| `make verify-locked PYTHON=.venv/bin/python` | PASS — 24 archives / 91 members、およびG2 identity全件 |
| `make verify-g3 PYTHON=.venv/bin/python` | PASS — 経済76,488、人口91,595、Access 254、L01 6,836 observations |

raw sourceはGitへ登録していない。実行ごとの派生Parquetと
`data/qa/g3_normalization_report.yml`もローカル再生成物であり、Gitの正本は変換コード、
テスト、仕様、判断記録である。

## 出力と粒度

| Local artifact | Grain | 件数 | 安全上の扱い |
|---|---|---:|---|
| `data/derived/economic_mesh_500m.parquet` | 経済センサスの都道府県成分 × 500m mesh | 76,488 | `mesh_code`単独を主キーにしない。366 meshは複数都道府県成分を持つ。 |
| `data/derived/population_mesh_500m.parquet` | 国勢調査の都道府県成分 × 500m mesh | 91,595 | 476 meshは複数都道府県成分を持つ。秘匿11,685、合算先9,116を数値0へ変換しない。 |
| `data/derived/station_access_observations.parquet` | confirmed station-line membership × S12 source feature | 254 | `allowed_score_domain=access`。duplicate/existence codeを保持する。 |
| `data/derived/land_price_points.parquet` | L01標準地 point | 6,836 | `allowed_score_domain=validation`。CoreScale入力ではない。 |

経済・人口meshの観測IDは`mesh_partition_observation_id`であり、
`source family + prefecture partition + mesh_code`からなる。各行には`source_raw_record_key`、
archive hash、基準時点、公表時点、raw token、numeric value、statusを保存した。`mesh_partition_count`、
`mesh_partition_codes_json`、`cross_partition_rollup_status`により、後続工程が成分の片方を
選択・重複削除・無根拠合算することを防ぐ。

## 500m meshの境界処理

[e-Statの提供単位説明](https://www.e-stat.go.jp/pdf/gis/teikyo_mesh_chigai.pdf)により、
県境をまたぐ同一meshの都道府県ZIP値は、全値の重複ではなく当該都道府県の寄与分であることを確認した。
そのため、G3の`cross_partition_rollup_status`は次の二値だけを許可する。

| Status | 意味 | G3で行うこと |
|---|---|---|
| `single_prefecture_component` | 取得範囲内で1都道府県成分だけが観測された | raw成分を保存する。全メッシュ値と推定しない。 |
| `requires_scope_aware_prefecture_component_sum` | 同じmeshに複数都道府県成分がある | 全メッシュ化の前に、公式行政界と対象scopeを用いて合算対象を固定する。 |

メッシュ幾何はJGD2011の第4次地域メッシュ規則から再構成したfull meshである。各成分の
幾何は都道府県境界でクリップしていないため、`partition_geometry_status`は
`full_mesh_geometry_not_administrative_partition_clip`で固定している。

## 指標別の分離

- 経済センサス`T001163`は、定義PDFに基づく小売・宿泊飲食・生活関連サービス娯楽の
  事業所数／従業者数と全産業補助列だけを抽出した。
- 国勢調査`T001141`は`HTKSYORI`に従い、`0=observed`、`1=aggregation_destination`、
  `2=suppressed`を保持した。抑制元に数値が存在しても`resident_population_value`へ流入しない。
- S12の乗降客数はAccess専用であり、CoreScale列・候補surface列を生成していない。
- L01地価はvalidation専用であり、規模の入力・順序付けに使用していない。

## 次のゲート（G3.1）

1. 公式行政界データを、利用条件・基準時点・座標系・取得単位まで監査する。
2. 1都3県＋10kmとTX例外を、承認済み境界に対して明示的にclipする。
3. 都道府県mesh成分を、そのclipに対してのみscope-awareにroll upする。
4. rollup前後の合計、秘匿状態、境界mesh数を監査し、初めてcandidate activity surfaceへ渡す。

このゲートが通るまで、同一mesh codeを一本化したCore surface、中心地抽出、スコア、ランキングを
作成してはならない。
