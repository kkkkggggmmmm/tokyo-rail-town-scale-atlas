# Official correction and distribution recheck — 2026-08-30

**Scope:** official catalog, correction/revision, update, and terms pages for the five
Phase 1 source families. This is a metadata recheck only: no raw archive was downloaded,
unpacked, or hash-verified in Phase 0.

**Result:** **PASS at catalog level, with acquisition-day source-lock gates.**

## Findings

| Source | Official recheck result | Phase 1 consequence |
|---|---|---|
| N02 railway 2025 | The catalog still names the 2025 edition, its 2025-12-31 reference date, and CC BY 4.0. The current correction page has no `N02-25` entry. | Acquire only the current official archive; record final bytes and recheck the correction page on the same day. |
| S12 ridership FY2024 | The catalog still names FY2024 as latest, warns of non-public stations and a one-year source-data lag, and licenses the data CC BY 4.0. The current correction page has no `S12-25` entry. | Retain the correction-day recheck because the official log shows an older `S12-24` attribute correction (2026-01-16). Preserve existence and duplicate codes before parsing counts. |
| 2021 Economic Census mesh | e-Stat’s update page now records detailed JGD2000/JGD2011 mesh downloads (2025-01-23) and prefectural downloads (2025-10-09), in addition to the 2024-09-25 broad-class publication. | Store these as **distribution events**, not as the 2021-06-01 reference date. Lock the selected 500m table definition and source bytes. |
| 2020 Census mesh | e-Stat records JGD2011 downloads from 2024-03-14 and 1km/500m/250m prefectural downloads for JGD2000/JGD2011 from 2025-10-09; the newer 125m reference-table addition is separate. The 500m JGD2011 population/household table is `T001141` (not the age table `T001192`). | Continue to use only registered 500m tables for Phase 1, pinning `T001141`. Do not let a later distribution event masquerade as the 2020-10-01 census reference date. |
| L01 land price 2026 | The catalog still identifies 2026 as the latest edition and 2026-01-01 as its reference date. The official correction log says that on 2026-04-24 `L01-26_13_GML.zip`, `L01-26_53_GML.zip`, and `L01-26_GML.zip` were corrected for part of Tokyo’s address data. | **Hard gate:** acquire and hash only the post-correction `L01-26_13_GML.zip`; stop and re-audit if the correction page changes or the archive changes after lock. |

## Evidence URLs

- [N02 railway 2025 catalog](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N02-2025.html)
- [S12 station ridership FY2024 catalog](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-S12-2024.html)
- [L01 land-price 2026 catalog](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-L01-2026.html)
- [National Land Numerical Information correction log](https://nlftp.mlit.go.jp/ksj_error.html)
- [e-Stat update information](https://www.e-stat.go.jp/help/data-definition-information/update-information)
- [e-Stat terms of use](https://www.e-stat.go.jp/terms-of-use)

## What this check does not prove

1. It does not prove the checksum or archive-member list of a future download.
2. It does not establish that an archive lacks a later, unlisted correction.
3. It does not replace the Phase 1 G0/G1 source-lock procedure.

## Required acquisition-day record

For every downloaded archive or table, record the final URL, retrieval timestamp, HTTP
metadata where available, byte size, SHA-256, member list, encoding, source reference date,
publication/distribution event, and the correction/revision page checked. If any of these
conflicts with `SOURCES.yml`, stop before transformation and issue a new audit entry.
