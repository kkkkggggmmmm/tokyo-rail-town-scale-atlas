# PROJECT_STATE

## Town grouping and comparison-scope correction — 2026-09-12

- Owner identifies the incompatible ranking units: Ginza region versus a Shinjuku exit, a shopping street or an individual mall. Default regional-data entry now uses a town/area hierarchy; the source-level numeric table and tap-to-sort remain explicitly available as **公表地区の数値・並べ替え**, not a whole-town ranking.
- First eight editorial navigation groups: 新宿、銀座、池袋、渋谷、日本橋、原宿・表参道、六本木、吉祥寺. `dist/district-areas.mjs` freezes opaque browse IDs and explicit source-district references. These are related-district review lists, not canonical center IDs, approved center membership or a complete regional inventory. No name-pattern clustering or source-value modification occurs. Includes Shinjuku south-side references recorded under Shibuya ward and Ginza facilities recorded under 境界未定地域.
- **PARTIAL: town totals/rankings remain blocked on geographic membership, coverage and overlap evidence.** Every browse group has aggregationAllowed=false; parent values/ranks are not emitted. Source child figures, years and original suppression remain visible. A single source row called 銀座地域 is not promoted to a whole-town total. Areas outside the first eight remain accessible through all 2,706 source districts, with no invented town grouping.
- Official definition rechecked: https://www.stat.go.jp/data/e-census/2021/kekka/pdf/ricchi_riyou.pdf (pp.1–3). Shopping streets, qualifying malls and multi-establishment buildings can each be their own district; some districts cross municipalities. This does not prove duplicate establishments, but no blanket non-overlap guarantee or exact 2021 town-to-district coverage was verified. The existing workbook has names/IDs, not boundary geometry. Tokyo 2014 district list (https://www.toukei.metro.tokyo.lg.jp/syougyou/2014/sg14vv1400.csv) also lacks geometry and has changed district definitions; it is not substituted for a 2021 boundary source.
- Next evidence required: a reviewed 2021 source-district-to-town crosswalk with included/excluded districts, accounting for cross-boundary/underground facilities, geometric or assignment evidence for overlap and missing-component rules. Only then compute per-metric region totals and rank comparable regions; incomplete observed sums must not impersonate complete totals. No N03 acquisition, canonical identity merge or raw-input transformation is attempted.
- Validation: 19 JavaScript checks PASS; `make verify-fast` PASS. New checks cover all referenced source IDs, duplicate associations, cross-ward examples, withheld parent totals/ranks and URL state. All module syntax and unchanged five public JSON payloads PASS. Authored static site; browser and physical-device QA not requested/performed.

## Commercial-district numeric rankings — 2026-09-12

- **PUBLISHED v0.8**: https://tokyo-rail-town-atlas.dwdaai.chatgpt.site. Saved version 8 (`appgprj_6a9f389f781c8191b52856216aaa9b32~appgver_944a104c81a881919f3b1e66b220a8c1`), deployment `appgdep_6aa5cb84d4f481919febd1f23cd20efd` succeeded at 2026-09-12T22:00:49.682420+00:00. Exact deployed source `58d754dbdd4568d2b492dc6b29fa78204fb003ef`. The 20-file archive preserves all 19 public asset bytes and semantically identical hosting configuration. The initial local archive inspector expected the configuration at the repository root; it was corrected to the helper's normalized `dist/.openai/hosting.json` path and passed before deployment. This receipt-only commit changes no public assets.

- Owner requests tap-to-sort numeric headers in the regional commercial-district table. All five numeric columns now select descending order on first tap, toggle ascending on repeat, and show the active direction. The source order can be restored.
- Rankings apply to the full prefecture/query result before 30-row pagination. Same published values share competition rank (1, 1, 3); ranks follow the selected direction. Suppressed/unpublished values remain unranked at the end in both directions. Three-sector totals still require every sector, and below-rounding values keep their original label and source rounding semantics. No statistical values, definitions or source periods change.
- Independent district sort/direction persist in the URL alongside filters. Header IDs, keyboard focus and horizontal table scroll survive rerender; the selected column is highlighted and exposes aria-sort. A narrow rank column and explicit district-name width preserve mobile readability.
- Validation: 18 JavaScript behavior checks PASS, including all five actual-data rankings before pagination, missing/rounded/tied synthetic values and independent URL/header state. `make verify-fast` PASS after restoring the existing pinned Python dependencies. Entry assets, module syntax, whitespace and byte-for-byte conservation of all five public JSON assets PASS. Read-only review identified an inherited first-column minimum width; the rank/name selectors were corrected once. Static authored assets need no build step. Browser and physical-device QA not requested; not performed. No raw-input, ID, N03 or source-lock changes; locked-source checks are not newly claimed.

## Food, shopping and student theme layout v0.7 — 2026-09-12

- **PUBLISHED v0.7**: https://tokyo-rail-town-atlas.dwdaai.chatgpt.site. Saved version 7 (`appgprj_6a9f389f781c8191b52856216aaa9b32~appgver_e29925ea30488191911956d77ab399a6`), deployment `appgdep_6aa4efa59f3881918d88f7458d6a91bc` succeeded at 2026-09-12T06:22:40.919097+00:00. Exact deployed source `ccac0ff9ddfb320bfd6c5b2eef454a1979a1c6de`. All 19 public assets in the 20-file archive match pushed source bytes, and the packaged hosting configuration is semantically identical. This subsequent receipt-only commit changes no public assets.

- Owner supplies reference images `1000016579.png` and `1000016580.png`. Rebuilt the working surface around their compact blue/white panels and numbered sections: station search and short numeric selector at left, the existing geographic map in the middle, selected-station metrics at right. The full-width entry cards no longer precede the working surface; all destinations remain in navigation and theme controls. A fresh visit selects the existing 吉祥寺 record without changing the geography-only default map theme.
- Food/shopping: four colored raw-metric cards, two-sector composition, customizable comparison table, and clearly separate links to municipal cafe counts and official commercial-district sales/floor area. Student/education: measured resident summaries, resident count/share chart, explicit unavailable incoming-student panel, and actual verified school names/addresses/official walking-time facts. No reference-image example values, inferred facility totals, stock photos, invented campus paths or individual-shop shares were added.
- Mobile: keeps search and quick station choices above the map/list switch result; selected details now follow the map or list instead of covering the map with a fixed sheet. Theme controls scroll horizontally; summary cards remain readable, and detailed comparison tables retain horizontal scrolling. URL filters, camera, profile return, comparison pins and source definitions are preserved.
- Data conservation: the same five public JSON payloads are byte-for-byte unchanged against the canonical parent. No raw input, normalization, N03, source lock, observation, identity or score changes. Existing scale and scope limitations continue to apply.
- Validation: 32 existing JavaScript checks and three new display/selection checks PASS; eight public-payload Python checks PASS; source syntax, unique entry IDs, local entry assets and whitespace checks PASS. Read-only review found two concrete issues, fixed once each: an older high-specificity mobile CSS rule hid the relocated search; shared-mesh deduplication replaced a selected operator record. New regression coverage preserves the selected 東急渋谷 record and missing/zero/student-residence semantics. Browser and physical-device QA: NOT_CHECKED (not requested; buildless project has no supported agent preview). Authored static site requires no compilation. `make verify-fast` PASS after restoring the existing pinned requirements. Publication succeeded as recorded above; raw-source checks are not newly claimed.

## Connected atlas UI v0.6 — 2026-09-08

- **PUBLISHED v0.6**: https://tokyo-rail-town-atlas.dwdaai.chatgpt.site. Saved version 6 (`appgprj_6a9f389f781c8191b52856216aaa9b32~appgver_95bda58cc1fc8191bad43eb3758c1690`), deployment `appgdep_6aa096d9762c8191b1ebbf2e7b8edd50` succeeded at 2026-09-08T23:14:54.087784+00:00. Exact deployed source `22708003b14b7d783e088340444b863111252dbf`. Implementation continues under the Owner's existing MVP-publication authorization. The latest request prioritizes reference-image UI/UX, measurable profiles, connected map/list/comparison, and a complete line narrative.
- Added compact station/line/theme entry points and grouped search suggestions for stations, lines, official commercial districts and municipalities. Theme and concrete map-indicator controls stay visible. Detail filters use a draft and explicit result-count application; mobile uses a closable native bottom dialog. Conditions, comparison pins, station selection and separate exploration/line/profile map cameras persist in URL state. Selection can be closed without resetting the camera. List selection also exposes the mobile station preview.
- Map: preserved geographic GSI municipal boundaries, railways and stations. A single optional quantity theme uses area-proportional circles, with mesh/group deduplication and fixed all-pilot scales. Resident student share uses a fixed 0–100% color legend; missing and zero remain distinct. Selected scope is explicitly the statistical mesh's outer frame, not an inferred center boundary or a fully resolved prefecture-component polygon. N03 remains excluded.
- Profile: common six-metric summary, actual units/year/scope, all-pilot or same-line median and numeric coverage, separate two-sector retail/restaurant composition, independent Access observations, and resident/incoming/learning-resource student panels. Apparel is a subset of retail, not an extra composition sector. Same-size-town comparison remains unavailable because center classes are not established. Source definitions and original access details remain reachable.
- Lines: real map plus a full ordered-station chart for restaurant, retail and all-industry employment values and two-sector composition. Endpoints select an inclusive segment; values use fixed scales, and facts use deduplicated comparable meshes. Station selections connect chart, map and profile. Line comparison now leads with raw medians, units, coverage and explanatory synthesis; the unchanged old three-indicator rank is secondary. No center-area, density, inter-center distance, campus inflow, street GDP or office-floor estimate is fabricated.
- Data conservation: all five public JSON payload SHA256 values match v0.5 exactly. No acquisition, normalization, raw-lock modification or G2 recomputation occurred. Existing 226 station records, eight lines, 218 mesh contexts, official district sales, municipal cafes and verified learning resources remain at their original periods and geographic scope.
- Validation before publication: 32 JavaScript behavior tests and eight public-payload Python tests PASS; JavaScript syntax and whitespace checks PASS. Tests cover camera/URL contracts, count-circle area scaling, fixed legends, missing/zero, deduplication, scope frames, cohort medians, compositions, eight line sequences and classified suggestions. Read-only peer review identified synchronous resize camera events and draft-theme filtering; both were corrected. `make verify-fast` PASS. All 18 public archive assets match the pushed source byte-for-byte; the nineteenth file is semantically identical hosting configuration. The first archive check incorrectly expected identical JSON formatting; the helper minifies that configuration, so its parsed contents were verified without changing the archive. This receipt-only commit changes no public assets. Browser and physical-phone QA: NOT_CHECKED (not requested). Authored static assets require no compilation; raw-source verification is not newly claimed.

## Reference-led geographic explorer v0.5 — 2026-09-08

- **PUBLISHED v0.5**: https://tokyo-rail-town-atlas.dwdaai.chatgpt.site. Saved version 5 (`appgprj_6a9f389f781c8191b52856216aaa9b32~appgver_58fa23ac73248191b3995d89944d7b4d`), deployment `appgdep_6aa08a68a0408191bf194228cd1f557e` succeeded at 2026-09-08T22:21:53.563586+00:00. Exact deployed source `77ec2d41232a2c6a1adf98199612ad4942befca7`. The 18-file publication archive matched every public asset and the hosting configuration byte-for-byte. This subsequent receipt-only commit changes no public assets.

- Owner resumes the UI work and supplies ten reference screens. Implemented their blue/white visual language and dense, legible map/table layout using the existing official observations. Reference example values, photos, area polygons, invented composite ratings and unobserved student inflows are not imported.
- Main flows: searchable station list synchronized with the geographic map; food/shopping/work/student/transport themes; intersecting line, published-prefecture and saved-station filters; numeric sorting, selectable columns and current-result CSV; station profile with definitions and raw access notes; 2–4 station comparisons with a retail/restaurant scatter plot; geographic line view with ordered stations; dedicated commercial-district sales, municipal cafes and economic/education/safety context.
- Desktop keeps the station list beside the map. Mobile provides map/list switching, a station preview and bottom navigation. Saved stations stay in local device storage. URL state retains query, filters, theme, sort, columns, page, selected station and comparison pins. Profile/source return destinations are independent. Station profiles explain missing values and source-specific geography/year.
- Numerical constraints: the same five public JSON payloads are byte-for-byte unchanged from v0.4. No raw acquisition, ETL rerun, N03, new center geometry, statistical partition sum, or CoreScale change. Existing source identities, suppression, aggregation, rounded sales and all source periods remain intact. Station totals are explicitly station records. The prefecture facet refers to published mesh components, not independently determined station municipal membership.
- Access observations are shown without cross-operator ranking or proportional comparison bars. Student indicators remain resident university/graduate counts and same-area 2020 population shares. Municipal cafes and official district sales are kept separate from station meshes. The prior three-indicator route mean rank remains available in the line-comparison tab; no added student, apparel, access or education metric enters that composite.
- Read-only peer review found URL prototype keys, availability filtering under nonnumeric sorts, unstable line selection, return-destination overlap and missing access detail. Corrected each in this bounded UI change. The existing default-detail test was intentionally updated because regional data now opens the district-sales view; no statistical assertion was relaxed. New tests cover URL round trips, invalid keys, intersecting filters, pin limits, missing/zero, line order and the actual student values.
- Validation: `make verify-fast` PASS after installing the already-pinned pyarrow 18.1.0 dependency; 24 JavaScript behavior tests and eight public-payload Python checks PASS; syntax/diff checks PASS; all five public JSON SHA256 values unchanged. Browser and physical-phone QA: NOT_CHECKED (no browser QA requested). This is an authored static site with no compilation step. Raw-source verification is not newly claimed by this UI-only work. Production version 5 succeeded; the publication receipt above records the exact source.

## Additional measured indicators v0.4 — 2026-09-08

- **PUBLISHED v0.4**: https://tokyo-rail-town-atlas.dwdaai.chatgpt.site. Saved version 4 (`appgprj_6a9f389f781c8191b52856216aaa9b32~appgver_0d511748779481919cd821992efd5969`), deployment `appgdep_6aa0061da6e0819185049af2ffe05a34` succeeded at 2026-09-08T12:57:12.474900+00:00. Exact deployed source `252914f67b3edd1e53850069931a4f9a54311f67`. The subsequent receipt-only commit changes no public assets.

- Owner requests commercial GDP-like data, apparel/cafe counts, and a measurable student-town indicator. Added official district sales, apparel establishments, student residents and municipal cafe observations. N03 remains excluded; no center assignment, component sum or CoreScale change.
- Student data: 2020 Census T001144, four prefectures, 221 components in 216 of 218 station meshes. University/graduate resident counts and same-area population ratios are eligible for 217 of 226 station records. Example: 東海大学前 350/1,882=18.6%, 西千葉 367/2,895=12.7%. They describe resident students, not campus enrollment or incoming commuters. Suppression, aggregation and boundary cases are withheld from comparisons.
- Apparel: existing locked 2021 economic census T001163064, industry57 (textiles, clothes, shoes, accessories) added to station details/table/CSV and route medians.
- Sales: 2,706 official commercial districts in Tokyo/Saitama/Chiba/Kanagawa. Source table2 (0004015880), published 2024-06-25; sales refer to calendar2020. Three sectors only, not GDP/value added/all-industry sales. Source districts stay independent from canonical centers and stations. A searchable district table displays original sector values and a complete-case sum in 億円; any suppressed sector prevents the sum. Original sales0 means below rounding unit, not a true zero.
- Cafes: source table9-3 (0004005673), industry767, private, all employee sizes. Of 258 municipality/ordinance-city ward observations, 252 numeric and six symbol-unresolved null values. Publication 2023-06-27; reference 2021-06-01. No municipal-to-station allocation and no city-plus-ward sum.
- Existing three-indicator route mean rank remains based on restaurant/retail/employee medians. Added apparel and student medians are displayed separately with valid observation counts. No claim of campus inflow, office floor area, street GDP or educational quality.
- Six new original files are durably checkpointed as `libfile_05297e1693f88191b06a782927344ce6` (archive SHA256 `04e5e3a9dd830d9a5097477428d7ac5fa96dbfa040462e72808dcb2584a0ac42`). `data/manifests/public_supplements.yml` freezes individual hashes, bytes, source terms and dates. Regenerate with `python scripts/build_public_supplements.py`; restore the originals first. No network or automatic retry in this regeneration command.
- Validation: `make verify-fast` PASS, `make verify-locked` PASS (24 original archives/91 members and accepted G2 identities), six supplemental SHA256/byte checks and regeneration PASS, 14 JavaScript checks and eight public-data Python checks PASS, syntax/diff checks PASS. Independent read-only review covered 2,706 district renderings, 226 student details, source scope and UI event references. Two test assumptions (substring search also matches 山王銀座地域; aggregation destinations retain their numeric source value) were corrected without altering source observations. Browser/physical-phone QA: NOT_CHECKED. Static authored assets have no compile step. Production v0.4 succeeded. The 17-file archive matched all public assets byte-for-byte and preserved the configured static hosting settings.

## Quantitative map implementation — 2026-09-08

- **PUBLISHED v0.3**: https://tokyo-rail-town-atlas.dwdaai.chatgpt.site . Saved version 3 (`appgprj_6a9f389f781c8191b52856216aaa9b32~appgver_7fd0a547c83c81918df8d7cfe112c98e`) deployed successfully as `appgdep_6a9ff97dd5448191b9cfa67d0128e583` at 2026-09-08T12:03:20Z. Exact deployed source: `77fd9171670dab1ee26c3ff03a3655f527024b76`. This receipt-only commit does not change deployed assets.

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

## v0.3 implementation receipt

- Implemented geographic GSI map and 226 canonical station records in eight locked public segments, with 210 S12 numeric observations / 16 duplicate-only nulls and 218 station-containing mesh contexts. Retained 220 economic and 221 population prefecture components; no boundary allocation or rollup.
- Added approved 7 municipal/town economic observations, 2 municipal crime counts, and 7 verified school campuses. Unavailable exam rates, center GDP/sales and office floor area remain explicit missing values.
- Route comparison uses displayed 2021 raw medians and `route_station_context_mean_rank_v1` (equal average of three within-eight-route ranks; >=90% coverage). It is not CoreScale or an overall residential/education/safety ranking. Transport is not a commercial-score input.
- Reproducible generators: `scripts/build_public_quantitative.py` and `scripts/build_public_context.py`; public CSV export and downloadable SVG. Source/use records under `data/reference/quantitative/`; detailed receipt in `docs/QUANTITATIVE_MVP_2026-09-08.md`.
- Full recovered original archive checkpoint: `libfile_167b01d57458819180d11aafb5569995` (24 archives); source lock unchanged. Required fast/locked/G3 checks and 9 JS behavior tests PASS. Browser and physical-device QA NOT_CHECKED. Publication succeeded; exact receipt appears at the top of this file.
