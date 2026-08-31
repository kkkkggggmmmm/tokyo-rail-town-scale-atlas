# Changelog

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
