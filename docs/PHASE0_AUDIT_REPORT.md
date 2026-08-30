# Phase 0 Audit Report

**Project:** 東京圏 駅まちスケール・アトラス
**Audit date:** 2026-08-30
**Decision:** Phase 1 may start only through the acquisition and identity gates below
**Public ranking/UI:** out of scope and not produced

## Executive decision

5つの公的データ群は、公式配布元・粒度・時点・利用条件・欠損表現を確認できた。
カタログ監査時点で利用条件不明のソースはない。CoreScaleへ投入できる主データは
2021経済センサス500m meshで、2020国勢調査は居住context、N02は鉄道正本、
S12はAccess、2026地価公示は検証点に限定する。

Phase 0で最も重要な修正は、N02/S12の出典コードをcanonical IDにしなかったこと、
および `NULL`・秘匿・非公表・該当なし・真の0をschema上で分離したことである。
これにより、データ取得前のSTOP条件は回避された。ただしPhase 1実体検査で未知token、
alias衝突、訂正版不一致が見つかった場合は自動的に停止する。

## Required-output status

| Required output | Artifact | Status |
|---|---|---|
| Phase 0 audit report | this document | complete |
| Source manifest | `SOURCES.yml` | complete; bytes/checksums await gated download |
| Data dictionary | `DATA_DICTIONARY.md` | complete |
| Canonical schema | `schema/canonical.sql` | complete and executable fixture-tested |
| Pilot scope map | `docs/pilot_scope_map.svg` | complete; schematic |
| Golden Eval registry | `data/reference/GOLDEN_EVALS.yml` | 60 candidates, 45/15 split |
| Phase 1 execution plan | `docs/PHASE1_EXECUTION_PLAN.md` | complete |
| Pilot corridor registry | `data/reference/PILOT_LINES.yml` | exactly 8 corridors fixed |

The earlier v0.1 concept listed a populated `station_line_crosswalk.parquet` as a Phase 0
artifact. It is deliberately not fabricated here: creating it requires N02 records, while
the work-start instruction requires the identity system to be fixed before collection.
This phase fixes the crosswalk view and required fields; Phase 1 Gate 2 produces the first
populated Parquet. An empty file would falsely imply that normalization had succeeded.

## Official correction/distribution recheck

The official pages were rechecked on 2026-08-30 before external Phase 1 acquisition starts.
The full, date-bounded record is
[`OFFICIAL_CORRECTION_RECHECK_2026-08-30.md`](OFFICIAL_CORRECTION_RECHECK_2026-08-30.md).
The result is clear at catalog level: the current correction log lists no `N02-25` or
`S12-25` entry, while it explicitly lists a 2026-04-24 correction to the Tokyo L01-26
archive. The latter makes post-correction bytes a hard acquisition gate. e-Stat’s newer
events are distribution additions; they are recorded separately and do not change either
survey’s reference date. No raw archive was downloaded or hash-verified in Phase 0.

## Source audit summary

| Source | Reference time | Publication/distribution | Grain | Terms | Missingness risk | Permitted role | Audit result |
|---|---|---|---|---|---|---|---|
| N02 railway, FY2025 | 2025-12-31 snapshot | catalog updated 2026-04 | station/rail line features; JGD2011 | CC BY 4.0 | absent feature/attribute; source codes unstable as identity | rail network and alias seed | usable with controls |
| S12 ridership, FY2024 | FY2024 | catalog updated 2026-04 | station × operator/route record; line geometry | CC BY 4.0 | no data, nonpublic, station absent, duplicate record | Access only | usable with controls |
| 2021 Economic Census mesh | 2021-06-01 | 2024-09-25; detailed mesh 2025-01-23; prefectural download 2025-10-09 | 500m fourth-level mesh; JGD2011 | e-Stat terms, CC BY 4.0 compatible | `X`, `...`, `-`, blank; classification gaps | CoreScale/Type | usable with controls |
| 2020 Census mesh | 2020-10-01 | 2022-07-27; JGD2011 download 2024-03-14; prefectural download 2025-10-09 | 500m fourth-level mesh | e-Stat terms, CC BY 4.0 compatible | suppressed source and aggregation destination | resident context/type | usable with controls |
| L01 land price, 2026 | 2026-01-01 | 2026-03-18; known correction 2026-04-24 | standard-land point; JGD2011 | CC BY 4.0 | no nearby standard point; nullable attribute | validation/context only | usable after corrected bytes locked |

## 1. N02 railway data

Official catalog: [国土数値情報 鉄道データ 2025年度](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N02-2025.html)
Product specification: [KS-PS-N02 v3.1](https://nlftp.mlit.go.jp/ksj/gml/product_spec/KS-PS-N02-v3_1.pdf)

### Availability and grain

- Nationwide GML ZIP is listed by the official catalog and is small enough for a deterministic
  Phase 1 acquisition job.
- The 2025 edition represents the network at 2025-12-31; “2026-04” is distribution/catalog
  timing, not the railway reference year.
- Stations are line features attached to railway data. They are not entrance points or
  station-building polygons.

### Identity audit

`N02_005c` station code is a source-edition identifier assigned from station latitude order.
`N02_005g` groups same-name stations within 300m and uses a source-defined representative
code. They are useful crosswalk seeds but fail as permanent IDs because:

- coordinates and membership can change;
- different-name transfers are not grouped;
- same-name proximity is not proof of one paid-area/transfer complex;
- code continuity across releases is not guaranteed by the grouping rule.

**Decision:** mint opaque `station_id`, `station_group_id`, and `hub_id`; retain every N02
key in `entity_alias` by release.

### Terms and gaps

2020-onward national land numerical information is distributed under CC BY 4.0, with
attribution, modification notice, and third-party-rights review under the
[official terms](https://nlftp.mlit.go.jp/ksj/other/agreement_01.html). Missing attributes or
unmatched features are `source_absent`, never zero.

## 2. S12 station ridership

Official catalog: [国土数値情報 駅別乗降客数 2024年度](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-S12-2024.html)
Product specification: [KS-PS-S12 v3.3](https://nlftp.mlit.go.jp/ksj/gml/product_spec/KS-PS-S12-v3_3.pdf)

### Availability and grain

The latest listed statistical period is FY2024; the official page is updated/distributed
in 2026-04. The page also warns that operator aggregation criteria are not standardized.
Station/operator/route records may duplicate the same underlying station traffic.

### Missingness audit

Official code lists distinguish:

- [data available / data absent / nonpublic / station absent](https://nlftp.mlit.go.jp/ksj/gml/codelist/RailwayExistenceCd.html);
- [current record / duplicated on another route / station absent](https://nlftp.mlit.go.jp/ksj/gml/codelist/RailwayDuplicateCd.html).

These codes override naive blank handling. A nonpublic station is not ridership zero, and a
duplicate row is not another quantity to add.

**Decision:** S12 is eligible only for `AccessPower`, transport-town gap, and validation.
Any path from S12 to `CoreScale` fails validation.

## 3. 2021 Economic Census regional mesh

Official catalog: [e-Stat statistical GIS, 2021 Economic Census](https://www.e-stat.go.jp/gis/statmap-search?toukeiCode=00200553&toukeiYear=2021)
Official result page: [2021 Economic Census mesh publication](https://www.stat.go.jp/data/mesh/r3_w.html)
Definitions: [500m broad industry](https://www.e-stat.go.jp/help/data-definition-information/downloaddata/T001162.pdf), [500m middle industry](https://www.e-stat.go.jp/help/data-definition-information/downloaddata/T001163.pdf)

### Availability and grain

JGD2011 500m fourth-level mesh tables are available. The reference date is 2021-06-01 and
the broad-industry mesh result was published on 2024-09-25. e-Stat subsequently registered
detailed JGD2000/JGD2011 download availability on 2025-01-23 and prefectural downloads on
2025-10-09. These are distribution events, not new observations. Middle-industry detail is
preferred because it can separate retail from wholesale more cleanly; broad-industry is a
registered fallback.

### Coverage and gaps

The public tables provide establishments and employees for consumer-facing industries,
but do not represent individual shops or exact streets. Official usage notes document
classification gaps, excluded activities, comparability changes from corporate-number
coverage, and suppressed values. In the source notation:

- `X` is suppressed;
- `...` is not surveyed;
- `-` is no applicable figure/zero denominator, not a universal numeric zero;
- numeric `0` is the only direct zero signal accepted by the generic parser.

**Decision:** this is the principal `CoreScale` surface. Suppressed values are not silently
imputed; sensitivity scenarios must expose their impact.

## 4. 2020 Census regional mesh

Official result page: [2020 Census mesh publication](https://www.stat.go.jp/data/mesh/r2_w.html)
Definition: [500m population/household table](https://www.e-stat.go.jp/help/data-definition-information/downloaddata/T001141.pdf)

### Availability and grain

The 2020-10-01 population census is available at 500m fourth-level mesh. The selected
population/household table is e-Stat `T001141` (JGD2011). Original mesh publication was
2022-07-27; JGD2011 download distribution began 2024-03-14 and
JGD2000/JGD2011 prefectural downloads were added on 2025-10-09. Those are separate
provenance events. The 2025-12-16 125m reference-table addition is not a Phase 1 input.

### Suppression handling

`HTKSYORI` identifies unadjusted (`0`), aggregation destination (`1`), and suppressed source
(`2`) mesh records; `HTKSAKI` and `GASSAN` preserve the destination/source relationship.
General totals such as total population have different suppression treatment from detailed
breakdowns. Reaggregating both source and destination would double count.

**Decision:** resident population is context/type input, not commercial mass. Suppression
relationships are first-class data.

## 5. 2026 land-price publication

Official catalog: [国土数値情報 地価公示 2026](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-L01-2026.html)
Announcement: [2026 land-price publication](https://www.mlit.go.jp/report/press/tochi_fudousan_kensetsugyo17_hh_000001_00078.html)
Correction log: [国土数値情報 訂正情報](https://nlftp.mlit.go.jp/ksj_error.html)

### Availability and grain

2026 values have a 2026-01-01 reference date and were announced on 2026-03-18. The catalog
offers nationwide and prefecture archives. The official correction log records a 2026-04-24
correction affecting Tokyo address data and nationwide packages.

**Decision:** Phase 1 pins only post-correction bytes and records SHA-256. Standard land is a
sparse point sample; absence of a nearby point is `source_absent`, not price zero. It is a
market-context/validation layer, never direct commercial size.

## Cross-source comparability decision

| Domain | Allowed Core-comparable inputs | Explicit exclusions |
|---|---|---|
| Scale — Activity Mass | 2021 Economic Census consumer-facing establishments/employees | S12, land price, uneven POI/PLATEAU, human flow |
| Scale — Extent | Supported contiguous Economic Census activity cells | final fixed-radius station circles |
| Scale — Intensity | Economic Census activity per supported active area | residential population as numerator |
| Type | size-residualized industry shares; Census context | raw total size as type label |
| Access | normalized S12, route/hub/network features | direct addition to Scale |
| Confidence | coverage, dates, suppression, boundary stability | popularity or prestige proxy |

## STOP-condition disposition

| STOP condition | Phase 0 evidence | Disposition |
|---|---|---|
| Terms unknown | Official terms URLs recorded for all five families | clear at catalog level; reconfirm on retrieval |
| Station/center ID normalization fails | Opaque IDs, release aliases, review queue, lineage schema defined | design passes; actual unmatched rows stop Gate 2 |
| Missing and zero indistinguishable | Explicit status enum and source token maps; SQL checks | pass; unknown token is fatal |
| Acquisition/publication year conflated | Separate reference/publication/retrieval fields in manifest/schema | pass |
| Non-comparable data enters Core | `metric_definition.allowed_score_domain` and manifest roles | pass; validator enforces exclusions |

## Open risks carried to Phase 1

1. Middle-industry 500m cells may have enough suppression to destabilize small centers.
2. Core 500m mesh may understate underground/vertical or single-building mall concentrations.
3. N02 source aliases will have ambiguous transfer cases requiring adjudication.
4. Continuous central Tokyo may remain sensitive to saddle threshold and hierarchy rules.
5. S12 operator comparability limits cross-operator Access interpretation.

These are model/data risks, not reasons to bypass the STOP controls. The Phase 1 plan tests
them with registered alternatives and holdouts.
