# Changelog

## 0.7.0 — 2026-09-05

- Audited the official N03 2026 administrative-boundary source for G3.1 and selected it as the technical boundary candidate for the 1都3県 union, 10km buffer, and TX corridor.
- Recorded the N03 CC BY 4.0 declaration together with its explicit GSI secondary-use caveat. Because the planned processed-vector/map use cannot be self-classified safely, N03 acquisition, clip/rollup, Core surface generation, and publication remain blocked pending an Owner-recorded official determination.
- Added a non-executable scope-rollup contract: component support is `mesh ∩ prefecture`, partial components cannot be area-weighted, TX cannot use a centroid proxy, and unavailable/aggregation-destination values cannot enter a Core sum.
- Added `make verify-g3-1` and clone-safe tests that prevent the pending N03 gate from being silently bypassed.

## 0.6.0 — 2026-09-05

- Recovered all 24 locked Phase 1 archives from their official URLs and revalidated their 91 ZIP members against the existing SHA-256 source lock.
- Rechecked current official catalog, terms, table-definition, and correction evidence. The post-2026-04-24 Tokyo L01 archive still matches the locked bytes; the current correction-log text was not treated as proof that no future/unlisted correction exists.
- Added G3 normalizers for 2021 Economic Census mesh, 2020 Census mesh, S12 Access observations, and L01 validation points, with raw token, status, reference period, publication period, and archive provenance retained.
- Recorded the official e-Stat rule that the same mesh code in two prefecture downloads is two prefecture-specific components, not a duplicate. G3 preserves those components and blocks whole-mesh rollup until official boundary clipping is audited.
- Added `make verify-g3` and G3-specific checks for component identity, missingness, GeoParquet metadata, S12 Access-only use, L01 validation-only use, and the unresolved boundary gate.
- Kept candidate surfaces, center polygons, scores, rankings, and public UI blocked.

## 0.5.0 — 2026-09-04

- Accepted GitHub `main@5c886415` as the canonical restart baseline after the unpushed historical local G3 commit `8ad4948` could not be retrieved from GitHub.
- Added clone-safe fast validation in GitHub Actions and pinned its small dependency set.
- Added `make verify-fast` and `make verify-locked`; the latter remains mandatory whenever exact external raw archives are available or transformed.
- Added an S12 regression test: a duplicate record whose raw token is `0` remains `duplicate_on_other_record` with null numeric value, never `observed_zero`.
- Kept G3, rankings, center polygons, and public UI blocked.

## 0.4.0 — 2026-08-31

- Closed all 12 Phase 1 G2 identity/hub reviews with operator-official evidence; review history remains in the queue with zero open rows.
- Confirmed nine existing hubs, added the two-group 朝霞台—北朝霞 hub, rejected 浅草（銀座線—TX）as an operational-transfer hub, and folded the manual 町田 case into its existing hub.
- Locked all eight exact service segments with ordered station-name and N02 source-key hashes.
- Corrected JR中央線快速 from 20 to 24 primary stations by adding 高円寺・阿佐ヶ谷・荻窪・西荻窪; the crosswalk increased from 229 to 233 rows.
- Advanced project state to `G2_PASS_G3_READY`; publication, ranking, final center polygons, and public UI remain blocked.

## 0.3.0 — 2026-08-30

- Advanced to Phase 1 G2 candidate review from the locked N02-25 source.
- Added persisted opaque ID registry and explicit eight-corridor identity rules.
- Generated the initial review-only station, station-group, hub, line, alias, and crosswalk Parquet artifacts; subsequent same-version candidate expansion reached 242 stations, 229 crosswalk rows, and 12 open reviews before G2 adjudication.
- Added G2 identity validator; ambiguous matches and hub confirmations remain queued.
- No center polygons, scores, rankings, or public UI were produced.

## 0.2.0 — 2026-08-30

- Started Phase 1 G0/G1 after the Phase 0 baseline.
- Rechecked and hashed official catalog, correction, terms, update, and definition pages.
- Corrected the 2020 Census 500m JGD2011 population table pin to e-Stat `T001141`; `T001192` remains the excluded age-class table.
- Acquired 24 official ZIP archives across N02, S12, L01, 2021 Economic Census, and 2020 Census; verified 91 members and locked SHA-256/HTTP/encoding metadata.
- Added reproducible acquisition, source-lock, official-recheck, and validation scripts. No station crosswalk, scoring, final polygons, ranking, or UI was produced.

## 0.1.1 — 2026-08-30

- Created and synchronized the public GitHub canonical repository.
- Rechecked official source catalog, correction, update, and terms pages before Phase 1 acquisition.
- Recorded the L01-26 Tokyo-address correction of 2026-04-24 as a hard source-lock requirement.
- Recorded e-Stat mesh distribution events separately from each survey reference date.

## 0.1.0 — 2026-08-30

- Initialized Phase 0 canonical repository.
- Audited N02, S12, 2021 Economic Census mesh, 2020 Census mesh, and 2026 Land Price Publication data.
- Defined immutable internal IDs plus source alias/history tables.
- Froze eight pilot corridors and a 60-center Golden Eval candidate registry.
- Selected multiscale density + persistence peaks + marker-controlled watershed as the Phase 1 primary candidate, with fixed-radius buffers retained only as a negative-control baseline.
- Kept ranking, final center classes, and public UI blocked.
