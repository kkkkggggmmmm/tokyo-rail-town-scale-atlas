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
