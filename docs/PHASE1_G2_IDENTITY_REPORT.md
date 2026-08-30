# Phase 1 G2 identity report — 2026-08-30

## 判定

**CANDIDATE_REVIEW（G2の候補生成完了、確定前）**。N02-25の駅地物を8つのpilot回廊へ切り出し、opaque ID、N02 alias、駅群seed、hub候補、crosswalk、レビューキューを生成した。

自動処理は同名300mのN02 group seedを候補として保持するだけで、station_group／hubの公開確定や異名乗換の自動統合を行わない。営業キロではなく、駅中心点間の測地線累積を候補距離として明示した。

## 件数

- pilot回廊: 8
- station node候補: 242
- station_group候補: 231
- hub候補: 9（全件 `candidate`、手動transfer evidence待ち）
- station-line crosswalk候補: 229
- identity review queue: 13（open 12）

## 成果物

- `data/derived/stations.parquet`
- `data/derived/station_groups.parquet`
- `data/derived/hubs.parquet`
- `data/derived/lines.parquet`
- `data/derived/station_line_crosswalk.parquet`
- `data/derived/entity_alias.parquet`
- `data/qa/identity_review_queue.parquet`
- `data/manifests/identity.phase1.yml`

## 未解決を残した理由

- 複数source aliasが異なるgroup seedを持つ場合は `ambiguous_match` として未選択。
- N02の同名300m groupはhub確定根拠ではないため、hub候補を全件手動レビュー待ちにした。
- 複数のphysical routeを束ねる京浜東北・根岸線は `candidate_review` とし、service stopの確認をG2レビューへ送った。
- 中央線快速の緩行駅はprimary crosswalkへ混入させず、`auxiliary_context` として候補駅へ残した。

## 次の作業

G2レビューでopen queueを解決し、駅・駅群・hubの手動根拠とroute segmentを確定する。確定後にG3でmesh/S12/L01を正規化する。現時点では中心地、スコア、ランキング、公開UIを生成していない。

参照: `data/reference/PHASE1_IDENTITY_RULES.yml`, `data/reference/PHASE1_IDENTITY_REGISTRY.yml`, `data/manifests/source_lock.phase1.yml`
