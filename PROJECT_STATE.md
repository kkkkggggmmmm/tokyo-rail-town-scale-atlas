# PROJECT_STATE

## Quantitative map implementation — 2026-09-08

- Owner explicitly replaces the schematic/reference-tag product with a geographic map of municipalities, railways and stations, measured station/town indicators, education and safety context, and a route-level synthesis. The public output scope is expanded accordingly; the earlier reference-only UI restriction is superseded by this instruction. Unmeasured quantities remain unavailable rather than being invented.
- The frozen original bundle has now been restored completely: 24 archives and 91 members pass `make verify-locked`, and G2's 242 stations / 233 crosswalk rows / eight segments / zero unresolved reviews pass. Current e-Stat terms retrieval and the first missing archive succeeded before a single no-retry recovery of the remaining inputs. The older incomplete-raw blocker below is historical.
- N03 is still excluded. Geographic context uses the GSI optimal vector tiles under its published use terms; this does not approve N03 or a statistical component rollup. Canonical station identities remain the accepted G2 IDs.
- Station-area statistics expose official 500m mesh observations with their prefecture partition, source year and raw/missing status. They are not center polygons or station sales. Cross-prefecture components are not summed. GDP, sales and office floor area are attached only to the exact region and definition supported by the source.
- The former `買い物 2/7` style candidate-tag counts are withdrawn. A route synthesis must show the numerical evidence and coverage. It must not turn missing education, economic output or safety inputs into zero or a fabricated all-purpose score.
- Source-specific unresolved terms, failed education/crime fetches, and inconsistent source values remain excluded individually. An unavailable requested indicator is described with its actual missing reason.

## Reference infographics v0.2 — 2026-09-07

- Owner requests data implementation and infographics. Added interactive reference-catalog charts: eight reference-feature counts, four prefecture counts, multiple-anchor-station count, candidate/station correspondence, and consistent per-route comparison bars. The three main navigation entries remain; charts are inside the comparison area.
- All counts are computed at runtime from the existing public allowlist, with candidate-ID deduplication. The full list contains 44 distinct candidates despite 50 route memberships; 29 have multiple distinct anchor names. Prefecture counts are Tokyo 23, Kanagawa 7, Saitama 7, Chiba 7. Feature labels overlap and are not adjudicated statistical classifications.
- Chart clicks filter the candidate list by feature, prefecture and anchor multiplicity; filters intersect and restore from the URL. Charts retain the selected route's whole-catalog denominator while the matching list is filtered. Detail diagrams are correspondence diagrams, not transfer or geographic evidence.
- No measured commercial, ridership, population or land-price values have been added. The 24-archive lock still requires 15 unavailable archives (six economic and nine population); the saved nine-archive checkpoint is not a full pass. Required `verify-locked` was neither bypassed nor reported as passing. N03 remains excluded; the old gate wording below is historical.
- Validation: `make verify-fast`, 10 JavaScript behavior tests, JavaScript syntax and diff whitespace checks PASS. Independent read-only review verified counts and 1,215 filter combinations; its one issue (a self-opening button in the detail diagram) was corrected. Static authored assets need no compile step. Browser and physical-phone QA remain NOT_CHECKED.
- Source branch: `work/public-explorer-mvp`. Public version 2 deployed successfully as `appgdep_6a9f3fd518a08191b60d29fe5ae20270`, source commit `82863fba02ae5cb226750e63dae47c79e4784e1d`. Live URL: https://tokyo-rail-town-atlas.dwdaai.chatgpt.site . This receipt-only change does not alter the deployed assets.

## Public explorer MVP v0.1 — historical deployment, 2026-09-07

- Live public URL: https://tokyo-rail-town-atlas.dwdaai.chatgpt.site
- Deployment confirmed succeeded: `appgdep_6a9f3a82c6e0819180165666b17041cd`; saved version 1; deployed source `54932258de2ff4bf51b47bf7e31456d047ba1a12`. Public audience confirmed. This subsequent status-only commit does not change the four deployed public assets.

- Owner explicitly requests an overall refocus and MVP publication. This activates a public **reference-catalog explorer**, superseding the historical UI/publication prohibition only for this bounded output.
- Product: interactive schematic route map, street/candidate details, route profiles, and comparison of 2–4 routes. Uses only the frozen Phase 0 pilot and calibration reference registries; 44 calibration candidates in 1都3県. Excludes GE045 (つくば) and all 15 holdouts.
- Reference candidates are not extracted canonical centers. Features remain editorial hypotheses; commercial size, Access, confidence, geography, interval distances, and classes are not estimated. Schematic positions have no geographic or distance interpretation. Candidate counts describe catalog coverage, never total center counts or route quality.
- No raw acquisition, G2 identity consumption/recalculation, mesh transformation, N03, source-lock changes, or blocked source-pilot draft promotion is included. Existing raw/identity/model gates remain in force for those workstreams.
- GitHub remains canonical. Source-based prototype and source-transfer drafts remain preserved separately, not applied to this clean public branch.
- Publication requires clone-safe checks, public-export validation, JS/asset checks, then a saved exact-source deployment. Browser/phone QA status must be reported separately.
- Release status: PUBLISHED_PUBLIC_EXPLORER_MVP. Required clone-safe checks, 3 public-payload checks, 5 JavaScript behavior checks, JavaScript syntax and local asset checks passed. Browser/phone QA: NOT_CHECKED. Statistical-scale product remains incomplete.


## Current work — 2026-09-06

- **Owner decision: N03を使用しない。** Below, the N03 application route is a historical record, not the next task. No N03 acquisition, geometry, or scope rollup is authorized.
- Working base: recovered GitHub `main@4ef1ee46a4f33482c13e1edb6daf725ec0189994`; branch `work/golden-eval-runner`. No canonical reset or acceptance of lost code is implied.
- Workspace maintenance removed the local unpushed checkpoints previously reported as `defcdc0` and `d3d9185`. Current GitHub branches and the saved-file search do not contain those implementations. They are not claimed as present or reproduced.
- Current authorized scope: an independent evaluation runner using the frozen registry and submitted candidate prediction files, plus synthetic tests. No locked raw inputs or G3 transformations are consumed or changed.
- Real-data extraction remains blocked until an N03-free component-support contract and the implementation baseline are reconciled and required raw gates pass. Previously passed historical data checks below have not been repeated in this workspace.
- Overall model acceptance, final rankings, final boundaries and public UI remain blocked. Candidate registry tags are not adjudicated type labels.
- Validation: 16 new evaluation-runner tests passed, including a corrected free-text holdout leakage case. Required clone-safe validation and CLI evidence are recorded for this change; raw-input and real-center evaluation are not claimed. Build/browser QA does not apply to this non-UI work.

## Historical state recovered from GitHub (2026-09-05)

```yaml
project_id: tokyo-rail-town-scale-atlas
repository_candidate: tokyo-rail-town-scale-atlas
state_version: 0.7.0
updated_at: 2026-09-05
phase: 1
phase_name: pilot-metric-normalization
phase_status: G3_1_BOUNDARY_SOURCE_AUDITED_USE_DETERMINATION_PENDING
identity_gate: PASS_2026-08-31
normalization_gate: PASS_2026-09-05_WITH_SCOPE_GATES
next_gate: G3_1_OWNER_GSI_USE_DETERMINATION_THEN_BOUNDARY_ACQUISITION_AND_SCOPE_AWARE_ROLLUP
canonical_baseline:
  branch: main
  commit: 8cd4ce08db4717296d50a6e49d020b7c3c670fdd
  accepted_at: 2026-09-05
  local_g3_commit_8ad4948: unavailable_not_canonical
execution_spine:
  fast_ci: R0_CONFIGURED_2026-09-04
  locked_input_validation: REQUIRED_OUTSIDE_GIT
  g3_local_derivative_validation: REQUIRED_AFTER_NORMALIZATION
release_status: NOT_PUBLISHABLE
ranking_status: PROHIBITED_IN_PHASE_1
ui_status: PROHIBITED_IN_PHASE_1
remote_repository_status: PUBLIC_MAIN_SYNCED
remote_repository_url: https://github.com/kkkkggggmmmm/tokyo-rail-town-scale-atlas
official_correction_recheck: LIVE_CATALOG_AND_BYTE_LOCK_RECONFIRMED_2026-09-05
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
| Live official recheck and raw recovery | Complete with a stated correction-log limitation; 24 recovery archives match the existing byte lock | `docs/OFFICIAL_RECHECK_2026-09-05.md`, `data/manifests/source_lock.phase1.yml` |
| Phase 1 G3 normalization | Complete as local, review-only derivatives; 76,488 economic components, 91,595 population components, 254 Access observations, 6,836 L01 points | `scripts/normalize_phase1_g3.py`, `scripts/validate_phase1_g3.py`, `docs/PHASE1_G3_NORMALIZATION_REPORT.md` |
| Phase 1 G3.1 N03 boundary audit | Complete as a stop-gated audit; source granularity/time are suitable but intended GSI secondary-use determination is pending | `docs/PHASE1_G3_1_BOUNDARY_AUDIT.md`, `data/reference/G3_1_BOUNDARY_SOURCE_AUDIT.yml`, `data/reference/G3_1_SCOPE_ROLLUP_CONTRACT.yml` |

## Phase 0 decision

**GO to Phase 1, with gates.** All five source families are obtainable and their usage terms are identifiable. Missingness can be represented without zero-imputation. The N02 source codes are not accepted as durable canonical IDs; the alias-registry design is therefore mandatory before acquisition is promoted into canonical tables.

## Phase 1 gates remaining after G3.1 audit

1. G3.1: obtain and record an official determination for the intended N03 secondary use, then acquire and lock the boundary source, clip the 1都3県＋10km/TX scope, and perform an explicit scope-aware rollup of e-Stat prefecture mesh components.
2. G4–G6: compare center challengers, adjudicate Golden Evals, and record a method-selection decision.

## Current blockers and non-blockers

- **Resolved external work:** public canonical repository is [kkkkggggmmmm/tokyo-rail-town-scale-atlas](https://github.com/kkkkggggmmmm/tokyo-rail-town-scale-atlas); `main@8cd4ce0` contains the R0 canonical reset and confirmed G2 identity artifact set.
- **Resolved source audit:** official catalog, correction, terms, update, and definition pages were rechecked and hashed on 2026-08-30. The 500m JGD2011 population input is pinned to e-Stat `T001141`; `T001192` is explicitly excluded because it is the age-class table.
- **Resolved acquisition:** 24 official ZIP archives (38,883,077 bytes) passed byte-size/CRC/path checks and are recorded in `data/manifests/source_lock.phase1.yml`; 2026-09-05 raw recovery reproduced those exact bytes. Originals are read-only outside Git.
- **Resolved G2 gate:** all 12 identity/hub reviews are reason-coded and resolved. Nine existing hubs plus 朝霞台—北朝霞 are confirmed from official transfer evidence; 浅草（銀座線—TX）remains separate and the manual 町田 case resolves to the existing hub.
- **Resolved service scope:** all eight exact segments are locked. JR中央線快速 was corrected from 20 to 24 primary stations before acceptance; all other candidate sequences were confirmed.
- **Resolved execution baseline:** `main@8cd4ce08` is the canonical restart point. The historical local commit `8ad4948` is unavailable from GitHub and is not a source of truth; its behavior may only be recovered through independently supplied bytes and validation.
- **Execution rule:** fast CI validates clone-safe contracts. Any G3 or raw-input change additionally requires exact-byte `verify-locked` validation outside Git.
- **Resolved G3 input semantics:** prefecture-level e-Stat rows sharing a 500m `mesh_code` are official prefecture components, not duplicate rows. G3 preserves 366 economic and 476 population cross-prefecture mesh groups instead of dropping or prematurely summing them.
- **Current blocker:** N03 2026 is a suitable official boundary source, but its catalog warns that secondary use of the GSI-derived source may require a procedure. The project cannot self-determine whether the planned processed scope/vector use is exempt. Until the Owner records the official outcome, N03 is not acquired and no boundary buffer, component clip, or Core surface is generated.
- **Non-blocker:** no center transformation, ranking, final polygon, or public UI has been produced. G3 consumes the confirmed G2 crosswalk only for Access observations; publication remains blocked.
- **Known risk:** 500 m Economic Census cells limit Core boundary precision. Enhanced layers may refine geometry later, but may not back-propagate into a supposedly nationwide Core score without a new decision.

## STOP conditions carried forward

- Unresolved use terms
- Ambiguous station or center identity forced into a merge
- Loss of zero/missing/suppressed distinction
- Reference year presented as publication/model year
- Enhanced/local-only data introduced into Core

## v0.3 implementation receipt (pre-publication)

- Implemented geographic GSI map and 226 canonical station records in eight locked public segments, with 210 S12 numeric observations / 16 duplicate-only nulls and 218 station-containing mesh contexts. Retained 220 economic and 221 population prefecture components; no boundary allocation or rollup.
- Added approved 7 municipal/town economic observations, 2 municipal crime counts, and 7 verified school campuses. Unavailable exam rates, center GDP/sales and office floor area remain explicit missing values.
- Route comparison uses displayed 2021 raw medians and `route_station_context_mean_rank_v1` (equal average of three within-eight-route ranks; >=90% coverage). It is not CoreScale or an overall residential/education/safety ranking. Transport is not a commercial-score input.
- Reproducible generators: `scripts/build_public_quantitative.py` and `scripts/build_public_context.py`; public CSV export and downloadable SVG. Source/use records under `data/reference/quantitative/`; detailed receipt in `docs/QUANTITATIVE_MVP_2026-09-08.md`.
- Full recovered original archive checkpoint: `libfile_167b01d57458819180d11aafb5569995` (24 archives); source lock unchanged. Required fast/locked/G3 checks and 9 JS behavior tests PASS. Browser and physical-device QA NOT_CHECKED. Publication receipt follows after deployment.
