# PROJECT_STATE

```yaml
project_id: tokyo-rail-town-scale-atlas
repository_candidate: tokyo-rail-town-scale-atlas
state_version: 0.1.0
updated_at: 2026-08-30
phase: 0
phase_name: canonical-definition-and-availability-audit
phase_status: COMPLETE_LOCAL_CANONICAL_CANDIDATE
release_status: NOT_PUBLISHABLE
ranking_status: PROHIBITED_IN_PHASE_0
ui_status: PROHIBITED_IN_PHASE_0
remote_repository_status: NOT_CREATED
```

## Owner intent

東京圏の各駅について、駅に接続する商業中心地の規模とタイプを推定し、地図・沿線プロファイル・沿線比較として可視化する。最終的に「どの沿線に、どの規模・タイプの街が、どの程度の間隔で存在するか」を理解可能にする。

## Canonical decisions

1. 初期表示対象は1都3県。解析には周辺バッファを持たせる。
2. 表示入口は駅だが、計算正本は commercial center とする。
3. Scale、Type、Access、Confidenceを分離する。
4. 乗降客数を街の規模の代理変数として直接ランキングしない。
5. 固定半径円を最終的な中心地境界にしない。
6. データ年度を統合して「2026年値」などと表記しない。
7. Google Maps、食べログ等の無許可スクレイピングを行わない。
8. Core scoreは全域比較可能な公的統計を中心とする。
9. PLATEAU、POI、人流はEnhanced layerとして扱う。
10. GitHubをコード、変換処理、データ辞書、判断履歴の正本とする。

## Phase 0 completion ledger

| Requirement | State | Canonical artifact |
|---|---|---|
| Repository initialization | Local complete; remote pending | git repository / this file |
| Required governance files | Complete | root documents |
| Five-source availability audit | Complete at metadata/specification level | `SOURCES.yml`, audit report |
| Canonical schema | Complete candidate | `schema/canonical.sql` |
| Eight pilot lines | Frozen | `data/reference/PILOT_LINES.yml` |
| Pilot scope map | Complete, schematic only | `docs/pilot_scope_map.svg` |
| 60 Golden Eval candidates | Frozen candidate registry | `data/reference/GOLDEN_EVALS.yml` |
| Extraction algorithm comparison | Complete candidate decision | `CENTER_MODEL.md` |
| Phase 1 execution plan | Complete | `docs/PHASE1_EXECUTION_PLAN.md` |

## Phase 0 decision

**GO to Phase 1, with gates.** All five source families are obtainable and their usage terms are identifiable. Missingness can be represented without zero-imputation. The N02 source codes are not accepted as durable canonical IDs; the alias-registry design is therefore mandatory before acquisition is promoted into canonical tables.

## Remaining gates before Phase 1 processing

1. Create the remote GitHub repository and push the local canonical commit.
2. Download source archives and record byte size, SHA-256, retrieval timestamp, and any correction notice.
3. Prove station crosswalk behavior on a small fixture covering same-name, different-name transfer, rename, and ambiguous proximity cases.
4. Record every unresolved match as `unresolved`; do not force it into a station group or hub.

## Current blockers and non-blockers

- **Non-blocker:** the GitHub connector can read/write an existing repository but cannot create the absent repository in this environment. Local git initialization is complete.
- **Non-blocker:** source archives were deliberately not ingested in Phase 0; metadata, schemas, filenames, direct endpoints, and usage terms were audited.
- **Known risk:** 500 m Economic Census cells limit Core boundary precision. Enhanced layers may refine geometry later, but may not back-propagate into a supposedly nationwide Core score without a new decision.

## STOP conditions carried forward

- Unresolved use terms
- Ambiguous station or center identity forced into a merge
- Loss of zero/missing/suppressed distinction
- Reference year presented as publication/model year
- Enhanced/local-only data introduced into Core
