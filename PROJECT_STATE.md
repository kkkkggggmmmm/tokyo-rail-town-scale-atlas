# PROJECT_STATE

```yaml
project_id: tokyo-rail-town-scale-atlas
repository_candidate: tokyo-rail-town-scale-atlas
state_version: 0.1.1
updated_at: 2026-08-30
phase: 0
phase_name: canonical-definition-and-availability-audit
phase_status: COMPLETE_CANONICAL_BASELINE
release_status: NOT_PUBLISHABLE
ranking_status: PROHIBITED_IN_PHASE_0
ui_status: PROHIBITED_IN_PHASE_0
remote_repository_status: PUBLIC_MAIN_SYNCED
remote_repository_url: https://github.com/kkkkggggmmmm/tokyo-rail-town-scale-atlas
official_correction_recheck: PASS_2026-08-30
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
| Repository initialization | Complete; public GitHub `main` synced | remote repository / this file |
| Required governance files | Complete | root documents |
| Five-source availability audit | Complete at metadata/specification level | `SOURCES.yml`, audit report |
| Canonical schema | Complete candidate | `schema/canonical.sql` |
| Eight pilot lines | Frozen | `data/reference/PILOT_LINES.yml` |
| Pilot scope map | Complete, schematic only | `docs/pilot_scope_map.svg` |
| 60 Golden Eval candidates | Frozen candidate registry | `data/reference/GOLDEN_EVALS.yml` |
| Extraction algorithm comparison | Complete candidate decision | `CENTER_MODEL.md` |
| Phase 1 execution plan | Complete | `docs/PHASE1_EXECUTION_PLAN.md` |
| Official correction/distribution recheck | Complete; acquisition-day recheck remains mandatory | `docs/OFFICIAL_CORRECTION_RECHECK_2026-08-30.md` |

## Phase 0 decision

**GO to Phase 1, with gates.** All five source families are obtainable and their usage terms are identifiable. Missingness can be represented without zero-imputation. The N02 source codes are not accepted as durable canonical IDs; the alias-registry design is therefore mandatory before acquisition is promoted into canonical tables.

## Remaining gates before Phase 1 processing

1. On acquisition day, recheck official terms, source catalog/revision notices, and the correction log; then download source archives and record byte size, SHA-256, retrieval timestamp, and any correction notice.
2. Prove station crosswalk behavior on a small fixture covering same-name, different-name transfer, rename, and ambiguous proximity cases.
3. Record every unresolved match as `unresolved`; do not force it into a station group or hub.

## Current blockers and non-blockers

- **Resolved external work:** public canonical repository is [kkkkggggmmmm/tokyo-rail-town-scale-atlas](https://github.com/kkkkggggmmmm/tokyo-rail-town-scale-atlas); `main` contains the Phase 0 artifact set.
- **Resolved source audit:** official correction/distribution pages were rechecked on 2026-08-30. L01-26_13 requires the 2026-04-24 corrected bytes; no current correction-log entry was found for N02-25 or S12-25. This is a catalog-level result, not an archive hash verification.
- **Non-blocker:** source archives were deliberately not ingested in Phase 0; metadata, schemas, filenames, direct endpoints, and usage terms were audited.
- **Known risk:** 500 m Economic Census cells limit Core boundary precision. Enhanced layers may refine geometry later, but may not back-propagate into a supposedly nationwide Core score without a new decision.

## STOP conditions carried forward

- Unresolved use terms
- Ambiguous station or center identity forced into a merge
- Loss of zero/missing/suppressed distinction
- Reference year presented as publication/model year
- Enhanced/local-only data introduced into Core
