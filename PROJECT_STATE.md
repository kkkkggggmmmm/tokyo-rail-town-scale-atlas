# PROJECT_STATE

```yaml
project_id: tokyo-rail-town-scale-atlas
repository_candidate: tokyo-rail-town-scale-atlas
state_version: 0.5.0
updated_at: 2026-09-04
phase: 1
phase_name: pilot-metric-normalization-ready
phase_status: G2_PASS_G3_READY
identity_gate: PASS_2026-08-31
next_gate: G3_MESH_MISSINGNESS_NORMALIZATION
canonical_baseline:
  branch: main
  commit: 5c886415c66c1e829173716637234f5924919a7c
  accepted_at: 2026-09-04
  local_g3_commit_8ad4948: unavailable_not_canonical
execution_spine:
  fast_ci: R0_CONFIGURED_2026-09-04
  locked_input_validation: REQUIRED_OUTSIDE_GIT
release_status: NOT_PUBLISHABLE
ranking_status: PROHIBITED_IN_PHASE_1
ui_status: PROHIBITED_IN_PHASE_1
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

## Completion ledger

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
| Phase 1 G0/G1 source acquisition | Complete; 24 archives, 91 members, SHA-256 locked | `docs/PHASE1_G0_G1_REPORT.md`, `data/manifests/source_lock.phase1.yml` |
| Phase 1 G2 identity and exact segments | Complete; 242 stations, 231 station groups, 10 confirmed hubs, 233 crosswalk rows, 8 locked segments, 0 open reviews | `docs/PHASE1_G2_IDENTITY_REPORT.md`, `data/reference/PHASE1_G2_ADJUDICATIONS.yml`, `data/manifests/identity.phase1.yml` |
| R0 canonical reset | Complete; GitHub baseline, clone-safe CI, and raw-input validation split fixed | `decisions/DECISION_REGISTER.md`, `.github/workflows/fast-validation.yml`, `Makefile` |

## Phase 0 decision

**GO to Phase 1, with gates.** All five source families are obtainable and their usage terms are identifiable. Missingness can be represented without zero-imputation. The N02 source codes are not accepted as durable canonical IDs; the alias-registry design is therefore mandatory before acquisition is promoted into canonical tables.

## Phase 1 gates remaining after G2

1. G3: normalize mesh tables, official mesh geometry, S12 codes, and L01 points while preserving missingness.
2. G4–G6: compare center challengers, adjudicate Golden Evals, and record a method-selection decision.

## Current blockers and non-blockers

- **Resolved external work:** public canonical repository is [kkkkggggmmmm/tokyo-rail-town-scale-atlas](https://github.com/kkkkggggmmmm/tokyo-rail-town-scale-atlas); `main` contains the Phase 1 G2 adjudication and confirmed identity artifact set.
- **Resolved source audit:** official catalog, correction, terms, update, and definition pages were rechecked and hashed on 2026-08-30. The 500m JGD2011 population input is pinned to e-Stat `T001141`; `T001192` is explicitly excluded because it is the age-class table.
- **Resolved acquisition:** 24 official ZIP archives (38,883,077 bytes) passed byte-size/CRC/path checks and are recorded in `data/manifests/source_lock.phase1.yml`; originals are read-only outside Git.
- **Resolved G2 gate:** all 12 identity/hub reviews are reason-coded and resolved. Nine existing hubs plus 朝霞台—北朝霞 are confirmed from official transfer evidence; 浅草（銀座線—TX）remains separate and the manual 町田 case resolves to the existing hub.
- **Resolved service scope:** all eight exact segments are locked. JR中央線快速 was corrected from 20 to 24 primary stations before acceptance; all other candidate sequences were confirmed.
- **Resolved execution baseline:** `main@5c886415` is the canonical restart point. The historical local commit `8ad4948` is unavailable from GitHub and is not a source of truth; its behavior may only be recovered through independently supplied bytes and validation.
- **Execution rule:** fast CI validates clone-safe contracts. Any G3 or raw-input change additionally requires exact-byte `verify-locked` validation outside Git.
- **Non-blocker:** no center transformation, ranking, final polygon, or public UI has been produced. G3 may consume the confirmed G2 crosswalk, while publication remains blocked.
- **Known risk:** 500 m Economic Census cells limit Core boundary precision. Enhanced layers may refine geometry later, but may not back-propagate into a supposedly nationwide Core score without a new decision.

## STOP conditions carried forward

- Unresolved use terms
- Ambiguous station or center identity forced into a merge
- Loss of zero/missing/suppressed distinction
- Reference year presented as publication/model year
- Enhanced/local-only data introduced into Core
