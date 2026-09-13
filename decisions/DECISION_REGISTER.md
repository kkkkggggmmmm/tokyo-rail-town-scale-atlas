# Decision Register

## OWNER-2026-09-07-MVP — publish a bounded reference explorer

- Accepted instruction: 「全体の構成を見直して目標や完成品を思い出して、一旦MVP公開までやってほしい」.
- Publish the connected reference-catalog experience now: schematic route map → town guide → route profile → comparison. Existing pilot and calibration-only registries supply the reference content.
- Keep numerical commercial scale, L0–L6 classes, actual center boundaries, traffic power and confidence uncomputed. Do not substitute evaluation tags or candidate coverage for these measurements.
- Publish only 1都3県 calibration candidates (44). No holdout labels, comparative constraints, or expected model outputs enter the bundle. Reference membership is an evaluation selection, not a complete rail-service/center membership.
- The public bundle contains no locked raw inputs, no G2 output conversion, and no statistical derivation. Existing mandatory raw checks are unchanged and remain blocking for source work.
- This is an early explorer MVP, not completion of the original statistical atlas.


## OWNER-2026-09-06-N03 — N03 not adopted

- Status: accepted Owner instruction, 「N03使わない確定でいいよ」.
- Decision: N03 is excluded. The application-next-step and candidate-selection portions of DEC-0015 are superseded. Its prohibition on unaudited N03 processing remains protective historical evidence.
- Scope: no replacement boundary source or whole-mesh rollup is automatically approved by this decision. Reconcile an N03-free component-support contract before real-data extraction.
- Recovery: local unpushed checkpoints are unavailable after workspace maintenance. This branch adds an independent Golden Eval runner to recovered GitHub code without claiming restoration of those checkpoints.

## DEC-0001 — Computational unit

- Date: 2026-08-30
- Status: accepted
- Decision: `center` is the computational unit; stations are access/display nodes.
- Consequence: a center can link to multiple station groups and lines, and each line counts the center once.

## DEC-0002 — Stable identity

- Date: 2026-08-30
- Status: accepted
- Decision: N02/S12 station and group codes are source aliases, not canonical primary keys.
- Rationale: N02 station codes are assigned by latitude ordering and are release-bound; names and geometry can also change.
- Consequence: canonical IDs are minted once and mapped through dated source aliases. Ambiguity remains unresolved until adjudicated.

## DEC-0003 — Missingness contract

- Date: 2026-08-30
- Status: accepted
- Decision: preserve raw tokens and explicit observation statuses before numeric conversion.
- Consequence: absent, suppressed, non-public, not surveyed, not applicable, out of scope, and observed zero cannot collapse to the same value.

## DEC-0004 — Core boundary candidate

- Date: 2026-08-30
- Status: accepted for Phase 1 comparison, not final
- Decision: use multiscale mesh density, persistent peak detection, and marker-controlled watershed/component-tree boundaries as the primary candidate.
- Consequence: fixed-radius circles are diagnostic baselines only. Core boundary resolution is not represented as finer than its 500 m source support.

## DEC-0005 — Pilot lines

- Date: 2026-08-30
- Status: accepted
- Decision: freeze the eight corridors in `data/reference/PILOT_LINES.yml`.
- Consequence: the Tsukuba Express corridor extends into southwest Ibaraki as an analysis-only buffer test; the default display domain remains one metropolis and three prefectures.

## DEC-0006 — Golden Eval split

- Date: 2026-08-30
- Status: accepted
- Decision: freeze 60 candidates, with 45 calibration and 15 holdout cases.
- Consequence: holdout expectations cannot be used to tune thresholds or weights.

## DEC-0007 — Core/Enhanced boundary

- Date: 2026-08-30
- Status: accepted
- Decision: Economic Census and Census mesh inputs are Core candidates; N02 supplies topology; S12 supplies Access; land price validates but does not set size. OSM/POI, PLATEAU, human flow, and commercial floor area remain Enhanced.

## DEC-0008 — Crosswalk artifact timing

- Date: 2026-08-30
- Status: accepted
- Decision: Phase 0 fixes the crosswalk schema/view but does not emit a zero-row or fabricated `station_line_crosswalk.parquet`.
- Rationale: a populated crosswalk requires gated N02 acquisition after the canonical ID contract is frozen; an empty Parquet could be mistaken for completed normalization.
- Consequence: Phase 1 Gate 2 must create the first populated artifact and resolve or reason-code every pilot station.

## DEC-0009 — Official correction recheck and acquisition lock

- Date: 2026-08-30
- Status: accepted
- Decision: Catalog-level correction/distribution checks are versioned in `SOURCES.yml` and `docs/OFFICIAL_CORRECTION_RECHECK_2026-08-30.md`; actual archive bytes are accepted only after an acquisition-day recheck and source lock.
- Rationale: official pages can change after Phase 0 and a catalog check cannot prove the byte identity of a later download. The L01-26 Tokyo archive has an explicit 2026-04-24 address correction.
- Consequence: Phase 1 may not transform L01-26_13 without post-correction SHA-256 evidence. N02/S12 and e-Stat inputs must also record the current official revision/definition state at retrieval; distribution events never replace survey reference dates.

## DEC-0010 — 500m Census table pin

- Date: 2026-08-30
- Status: accepted
- Decision: Phase 1 uses e-Stat table `T001141` for 2020 Census JGD2011 500m population/household observations. Table `T001192` is the 500m JGD2011 age-class table and is not the population-total input.
- Rationale: the official e-Stat table registry distinguishes the population/household table from the age-class table; selecting by resolution alone would silently bind the wrong variables.
- Consequence: definitions, acquisition URLs, and source locks must record `T001141`; any T001192 artifact is outside the Phase 1 population input and must not be transformed into `resident_population`.

## DEC-0011 — G2 identity candidate and review boundary

- Date: 2026-08-30
- Status: accepted for candidate generation; adjudication closed by DEC-0012
- Decision: Phase 1 G2 mints persisted opaque IDs for the eight pilot corridors and keeps N02 station/route/group keys only as dated aliases. N02 same-name/300m groups create `station_group` candidates; they do not confirm a hub.
- Rationale: N02 source codes are release-bound, and proximity alone cannot establish an operational transfer relationship. Service corridors such as JR京浜東北・根岸線 also span multiple physical N02 route aliases.
- Consequence: unresolved station matches, service-scope choices, same-name collisions, and hub candidates remain in `data/qa/identity_review_queue.parquet`. G3 may not consume an unreviewed crosswalk as a confirmed identity layer.

## DEC-0012 — G2 hub adjudication and exact service-segment lock

- Date: 2026-08-31
- Status: accepted
- Decision: Close all 12 open G2 identity/hub reviews using the cited operator-official evidence in `data/reference/PHASE1_G2_ADJUDICATIONS.yml`. Confirm the nine existing same-name hub candidates and the different-name 朝霞台—北朝霞 hub; reject 浅草（銀座線—TX）as an operational transfer hub; resolve the manual 町田 candidate as a duplicate of the existing `004387` hub.
- Service scope: Lock the eight pilot segments at 24 / 21 / 42 / 21 / 47 / 39 / 19 / 20 stations for JR中央線快速, JR総武線各駅停車, JR京浜東北・根岸線, 東急東横線, 小田急小田原線, 東武東上線, 東京メトロ銀座線, and つくばエクスプレス respectively. Persist both ordered station-name and ordered N02 source-key SHA-256 locks.
- Rationale: An N02 same-name/300m seed establishes a review candidate but not an operational transfer. Operator-official transfer guidance is sufficient to confirm or reject the hub relation without inventing proximity rules. Exact segment membership follows the official named route nodes between frozen endpoints, not a single train class or timetable pattern.
- Correction: The JR中央線快速 candidate omitted 高円寺・阿佐ヶ谷・荻窪・西荻窪. Move these four from auxiliary context into the 24-station primary segment before locking. Keep the eight stations served only by the 中央・総武緩行 context outside the primary segment.
- Reconciliation: The current Tobu route page explicitly enumerates 39 named 池袋—寄居 station nodes, while a corporate overview reports an aggregate station count of 40. Record the discrepancy and use the operator's current route-specific enumeration for segment membership; the unexplained aggregate definition does not identify a missing node.
- Consequence: G2 is PASS with 242 stations, 231 station groups, 10 confirmed hubs, 233 confirmed crosswalk rows, eight locked segments, and zero open reviews. G3 may consume this identity layer. Publication, ranking, final center geometry, and UI remain blocked.

## DEC-0013 — Canonical reset and validation split

- Date: 2026-09-04
- Status: accepted
- Decision: Treat GitHub `main@5c886415c66c1e829173716637234f5924919a7c` as the sole canonical restart baseline. The historical local commit `8ad4948` is unavailable from GitHub and must not be reconstructed from memory, chat history, or inferred output counts.
- Rationale: raw archives and a local worktree are intentionally external to Git, and the unavailable local commit cannot establish reproducible ancestry. A clean clone must nevertheless verify all contracts that do not require raw bytes.
- Consequence: `make verify-fast` is required for every change and runs in GitHub Actions. `make verify-locked` is additionally required for changes that consume or alter locked raw inputs, source locks, G2 identity artifacts, or later derived transformations. Raw-byte absence is never a reason to report full validation as passed.

## DEC-0014 — Prefecture-mesh component preservation and scope-aware rollup gate

- Date: 2026-09-05
- Status: accepted
- Decision: Treat each e-Stat prefecture-download row as a `prefecture partition × mesh` observation. When the same fourth-level 500m `mesh_code` appears in more than one prefecture download, retain all components; do not deduplicate by mesh code, select a preferred prefecture, or create a whole-mesh sum before an audited administrative-boundary scope clip exists.
- Rationale: e-Stat's official [provider-unit note](https://www.e-stat.go.jp/pdf/gis/teikyo_mesh_chigai.pdf) states that prefecture downloads contain only that prefecture's contribution for a cross-prefecture mesh, while a first-level regional result contains the full mesh. It explicitly says the same principle applies to Economic Census establishment results. The locked raw bundle contains 366 economic and 476 population mesh codes with multiple prefecture components.
- Consequence: G3 uses `mesh_partition_observation_id = source family:prefecture partition:mesh code`, preserves raw token/status/provenance, and marks cross-border groups `requires_scope_aware_prefecture_component_sum`. `data/derived/*mesh*.parquet` is not a whole-mesh Core surface. G3.1 must audit an official administrative-boundary source and validate scope-aware clip/rollup before candidate activity extraction, score calculation, or center geometry begins.

## DEC-0015 — N03 boundary source selected, secondary-use determination is a hard gate

- Date: 2026-09-05
- Status: accepted stop gate
- Decision: Select the 2026 National Land Numerical Information administrative-area dataset (`N03-20260101`) as the candidate authoritative boundary source for the 1都3県 display union, 10km analysis buffer, and TX 5km geometry corridor. Do not acquire or process it until the Owner records the result of the applicable GSI procedure/confirmation for the planned derived geometry and public-map use.
- Rationale: The official N03 catalog identifies national polygon coverage, a 2026-01-01 reference date, JGD2011 geometry, and CC BY 4.0. It also states that its GSI-derived source may require a secondary-use application. The planned dissolve/buffer/intersection and potential vector/map publication is too specific to self-classify reliably as application-free.
- Consequence: The repository contains only the source audit and a non-executable scope-rollup contract. No N03 archive, polygon, component classification, or scope aggregate is in the source lock. When the decision is resolved, retain the official determination, attribution/modification wording, any approval number and distribution conditions before adding N03 to the locked raw scope. Partial `mesh ∩ prefecture` components are never area-weighted or fractionally allocated.


## DEC-0016 — Table-defined area sums, with geographic coverage still unverified

- Date: 2026-09-12
- Status: accepted for the Owner's explicit area-total/ranking request
- Decision: Publish the sum of all explicitly assigned Table 2 leaf districts in each fixed browse collection as **エリア合計（公表地区合算）**. Keep `aggregationAllowed=false` for whole-center geography; add `selectedDistrictSumAllowed=true` for this narrower mathematical scope. Do not label this the entire economy of an intuitive town. The eight rosters and scope notes live in `dist/district-areas.mjs`, version `selected-district-sum-v1`; no source ID is shared between collections. Changes to the roster require a versioned decision and reranking.
- Evidence: The [official workbook](https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040186981&fileKind=0), SHA256 `44d36113accd458cc8c9c4d5538a187fe72903beaa75002fc705e9f300cc9bb8`, was inspected directly in memory. 12,535 unique leaf IDs sum exactly to six national establishment/employee measures; those six also reconcile in each of four prefectures and in 215 target municipality groups (1,290 exact comparisons). Higher-level totals leave the leaf-ID column blank. This numerical accounting supports use as additive table components, while no explicit establishment-exclusivity statement or town boundary was verified. [Official usage notes](https://www.stat.go.jp/data/e-census/2021/kekka/pdf/ricchi_riyou.pdf) retain cross-municipality districts and rounded/suppressed observation semantics.
- Consequences: Only complete per-metric sums rank; suppressed or not-applicable cells prevent a complete total. Preserve all constituent observations, years, units, IDs and missing reasons; expose the full selected roster. No subtraction to recover suppressed figures. Same-value ranks are 1,1,3 and filters only select groups, never change their membership. No area-allocation, N03, canonical center merge, full-town coverage certification or raw source reprocessing is authorized.


## DEC-0017 — Extend explicit district collections to all four prefectures

- Date:2026-09-13
- Status:accepted for continued regional-total/ranking implementation
- Decision:`selected-district-sum-v2` extends the eight existing collections to26, using200 distinct IDs from the unchanged public Table2 data. Tokyo16/Kanagawa3/Saitama3/Chiba4; exact included IDs and exclusions remain in `dist/district-areas.mjs`. Existing eight collections retain their IDs and contents. No source row is duplicated across collections.
- Geographic limits:These names describe fixed published-district collections, not verified polygons. Keep `aggregationAllowed=false`. 横浜CIAL is not covered by the included rows; ambiguous 浦和/松戸 associations are excluded explicitly; 六栄会/川越名店街 geographic assignment is unverified. Do not present these omissions as source values of zero or a complete town inventory. No numeric-based removal of suppressed members.
- Computation:unchanged complete-case and same-period rules from DEC-0016. Rankable counts23 retail/19 food/12 personal/11 three-sector/22 floor out of26. Unavailable sums receive no rank and stay visible. Search never clips a collection to matching source districts. No canonical center, station or municipality-total reassignment.

## DEC-0018 — Cover all source stations within the requested metro reach

- Date: 2026-09-13
- Status: accepted for the Owner's explicit all-station acquisition request
- Scope: `NETWORK_SCOPE.json` fixes an approximate polygon including Chiba/Toke, Saitama/Omiya/Urawa/Higashi-Iwatsuki and Fujisawa/Shonandai/Katase-Enoshima. This is a browse/acquisition scope, not a municipal or center boundary. All1,569 N02-25 records inside it are included;23 historical outside records are retained. No N03.
- Identity: existing G2 aliases/opaque IDs win; new UUIDs are persisted separately. A source-key ambiguity blocks new publication. Existing8 ordered corridors remain frozen;118 formal route inventories have no inferred sequence. New `nrt_` IDs describe those browse inventories, not canonical service corridors.
- Statistics: extend exact locked N02/S12/T001163/T001141/T001144 sources to the additional station meshes. Preserve every raw token, year, prefecture component and suppression/aggregation marker. S12 remains Access-only and un-summed. Public base JSON and all existing identity/lock files remain byte-identical.
- Publication: authorized expanded station exploration, quantitative profiles and comparisons, with explicit missing records and the approximate scope disclosed. No new center boundaries, whole-town totals or score model.
