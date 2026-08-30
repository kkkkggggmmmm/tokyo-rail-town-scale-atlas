# Commercial Center Model

**Model specification:** `center-model/0.1.0`
**Phase:** 0 — algorithm candidates and acceptance protocol
**Production status:** not calibrated; no ranking may be published from this document

## 1. Unit of inference

`center` is a contiguous or hierarchically connected concentration of consumer-facing
commercial activity. Stations are entrances and transport nodes, not the unit whose
commercial scale is scored.

The model emits four independent products:

1. `CoreScale`: commercial mass, spatial extent, and intensity.
2. `CenterType`: size-residualized composition and morphology.
3. `AccessPower`: ridership, interchange, and network position.
4. `Confidence`: data coverage, freshness, missingness, and boundary stability.

No component of `AccessPower` is an input to `CoreScale`. Confidence changes how a
result is displayed and reviewed; it does not raise or lower its scale.

## 2. Input layers

### Core-comparable surface

The initial surface uses 2021 Economic Census 500m JGD2011 mesh observations that are
available under a common specification across the analysis extent:

- retail establishments and employees;
- accommodation/food establishments and employees;
- lifestyle/leisure establishments and employees;
- all-industry employment only as a type/context feature.

2020 Census resident population is a type/context and residential adjustment feature.
N02 supplies railway/station geometry and source aliases. S12 supplies Access only.
L01 land-price points validate market context only.

### Enhanced-only layers

OSM/open POI, PLATEAU, commercial-facility anchors, planning zones, and human-flow data
may refine a boundary or type only when their coverage is recorded. They may not alter
the nationwide-comparable `CoreScale` series unless a future model version first proves
uniform coverage and passes the same acceptance tests.

### Resolution guardrail

Core input is nominally 500m mesh. Smoothing may estimate a density surface, but a Core
boundary must not claim building-, street-, or entrance-level precision. Geometry finer
than the supporting cells is tagged `enhanced_geometry`; the unsmoothed support cells
remain recoverable.

## 3. Preprocessing contract

1. Validate source release, checksum, CRS, metric definition, and missing token.
2. Reproject calculation copies to a locally appropriate metric CRS; preserve source WKB.
3. Keep `observed_zero` separate from all unavailable statuses.
4. For each positive long-tailed feature: `log1p`, train-fold winsorization, median/MAD
   robust scaling, then a documented monotone 0–100 transform.
5. Fit all cut points and transforms on calibration data only. Holdout values do not
   influence parameters.
6. Do not interpolate suppressed Economic Census cells for Core scoring. Run bounded
   sensitivity scenarios instead.
7. Create 400m/800m/1,200m station summaries only as diagnostics; never use their circles
   as the final center polygon.

## 4. Candidate activity surface

At each mesh cell `g`, define a nonnegative candidate activity value:

\[
A_g = \sum_{k \in K} w_k\{\alpha_k z(\log(1+E_{gk}))
       +(1-\alpha_k)z(\log(1+N_{gk}))\}
\]

where `E` is employees, `N` is establishments, `K` contains the consumer-facing
industries, and all `w_k`/`alpha_k` are calibration parameters. The employee signal is
expected to receive more weight, but Phase 0 fixes no numeric industry weight.

Missing cells do not become zero. Candidate surfaces are calculated under at least:

- complete-case lower-support scenario;
- bounded suppressed-cell sensitivity scenario;
- broad-classification fallback scenario.

If center topology changes materially between these scenarios, boundary confidence is
reduced and the case enters manual review.

## 5. Extraction algorithms to compare

| ID | Method | Strength | Expected failure | Phase 0 role |
|---|---|---|---|---|
| A | Station buffers at 400/800/1,200m | Simple, interpretable baseline | Overlap, double count, cuts large centers, invents station-centric geometry | Negative control only |
| B | Thresholded mesh connected components | Reproducible and faithful to support cells | One large Tokyo component; threshold instability | Baseline |
| C | Multi-scale KDE + persistent peaks + marker-controlled watershed | Separates peaks while retaining continuous urban fabric; supports hierarchy | Bandwidth/saddle sensitivity; may over-split linear streets | Primary candidate |
| D | Weighted HDBSCAN/OPTICS on mesh centroids and permitted anchors | Finds irregular clusters, handles noise | Parameter sensitivity; awkward full-coverage polygons; POI bias if mixed | Challenger |
| E | Superlevel-set component tree with saddle persistence and graph region growth | Explicit hierarchy and split/merge history | More complex implementation and adjudication | Strong challenger |

The Phase 1 decision is not “choose C by preference.” Each candidate receives the same
inputs, Golden Eval split, stability perturbations, and manual boundary audit.

## 6. Primary candidate procedure (C)

### 6.1 Multi-scale surface

Generate density surfaces with bandwidth candidates no finer than the evidence supports,
initially 500m, 750m, and 1,000m. Normalize edge effects using the 1都3県 analysis buffer;
do not clip the density surface at the display boundary.

### 6.2 Persistent peak detection

Detect local maxima at each scale. Retain a marker only if it persists across adjacent
scales or is supported by a documented commercial-facility anchor. A station alone never
creates a commercial peak.

### 6.3 Marker-controlled watershed

Run watershed/region-growing from persistent markers. Candidate splits are determined by
peak prominence and saddle depth. Store the complete merge tree so one parameter change
does not erase the parent/child interpretation.

### 6.4 Boundary trimming and holes

Trim basins at an activity support threshold learned on calibration cases. Remove isolated
cells below minimum mass, but preserve linear corridors that meet continuity tests. Holes
are retained only when they have observed noncommercial support; missing cells do not
automatically create holes.

### 6.5 Hierarchy

- `parent`: a broad continuously urbanized complex, such as a multi-district city center;
- `center`: the default deduplicated unit used in line summaries;
- `subarea`: a stable peak or functional district within a parent/center.

The evaluation registry decides case by case whether Tokyo–Ginza or Ueno–Okachimachi,
for example, should be siblings, children, or separate centers. The algorithm may propose
the relation but cannot silently collapse the hierarchy.

### 6.6 Station linkage

Link a `station_group` to one or more centers using polygon containment, network walking
distance where licensed data exists, peak influence, and manual evidence. Roles are:

- `core`: station group is inside or immediately serves the main activity peak;
- `auxiliary`: meaningful secondary entrance;
- `edge`: on the estimated fringe;
- `transfer_only`: linked operationally but unsupported as a commercial entrance;
- `multi_entry`: one station group is a credible entrance to multiple centers.

Proximity alone does not establish a `hub`, and hub membership alone does not establish a
center link.

## 7. Center identity across model versions

Geometry is versioned independently from identity. An existing `center_id` may continue
when all of the following hold:

- the principal activity anchor is continuous;
- overlap and weighted-mass overlap exceed registered thresholds;
- the interpretation remains the same unit rather than a split/merge;
- no Golden Eval or manual adjudication contradicts continuity.

Thresholds are calibrated in Phase 1; none is fixed in Phase 0. A true split or merge
mints new `center_id` values and records `center_lineage`. Names and centroid coordinates
never determine continuity by themselves.

## 8. Scale candidate

After boundaries are accepted, calculate three independently inspectable components:

- **Activity Mass:** robust aggregate of consumer-facing employees and establishments;
- **Spatial Extent:** supported active area, commercial-axis length, and multi-peak reach;
- **Intensity:** activity per supported active area and peak concentration.

The owner-proposed initial combination is retained as a calibration hypothesis:

\[
CoreScale_{candidate}=0.50M+0.30E+0.20I
\]

It is not a final weight set or ranking. Phase 1 must publish component-level sensitivity,
leave-one-feature-out results, and pairwise Golden Eval performance before acceptance.

## 9. Type, Access, and Confidence

### Type

Cluster size-residualized industry shares and permitted morphology features. Human reviewers
name clusters only after inspecting holdout confusion. Candidate labels are urban mixed,
shopping, food/night, business, tourism/leisure, local-life, and transport interchange.

### Access

Use S12 only after duplicate/existence code normalization, then combine the log-transformed
traffic signal with route count, interchange evidence, and line position. Publish the
source reference period and operator comparability caveat.

### Confidence

Keep at least these inspectable components:

- source completeness and suppression exposure;
- temporal alignment/freshness by source, not a single year label;
- boundary stability across scales and perturbations;
- station/center identity resolution status;
- Enhanced-layer dependency.

The overall confidence aggregation is a model parameter, not a substitute for component
flags.

## 10. Evaluation protocol

### Boundary tests

- intersection-over-union and weighted-mass overlap against adjudicated polygons;
- variation of information for parent/child partitions;
- stability under bandwidth, threshold, missingness, and edge-buffer perturbations;
- explicit inspection of all candidate L5/L6-equivalent large centers, without assigning
  those public classes in Phase 0.

### Pairwise/type tests

- all hard structural/pairwise constraints pass;
- at least 85% of soft pairwise constraints pass;
- holdout type-label agreement reaches at least 80%;
- every failure is written to the decision register, not patched invisibly.

### Adversarial cases

The 60-case registry deliberately includes continuous central Tokyo, multi-station centers,
one-station/multi-center entrances, transfer-dominant nodes, linear shopping streets,
mall-led suburbs, office districts, tourism districts, and small station fronts.

## 11. Phase 1 model selection rubric

| Criterion | Weight in selection | Minimum gate |
|---|---:|---|
| Hard topology/pairwise constraints | gate | 100% |
| Soft pairwise constraints | gate | ≥85% |
| Holdout type agreement | gate | ≥80% |
| Boundary agreement | 30% | No systematic major-case failure |
| Perturbation stability | 25% | Instability flagged, not hidden |
| Duplicate-free line linkage | 20% | 100% |
| Missingness robustness | 15% | No NULL-to-zero path |
| Interpretability/operability | 10% | Reproducible parameter manifest |

The percentage weights compare algorithms only after every gate passes.

## 12. STOP conditions

Stop the pipeline before scoring when any of the following is true:

1. A source's reuse terms or third-party rights are unresolved.
2. A source station/line key cannot be mapped uniquely or queued as an explicit unresolved case.
3. A raw missing token cannot be mapped without treating it as zero.
4. Reference, publication, and retrieval dates are conflated.
5. A nonuniform POI/PLATEAU/human-flow layer is entering CoreScale.
6. A fixed station radius is being written as the final center boundary.
7. A center split/merge would overwrite prior identity or geometry history.
