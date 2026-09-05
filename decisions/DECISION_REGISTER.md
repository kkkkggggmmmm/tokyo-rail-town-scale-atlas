# Decision Register

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
