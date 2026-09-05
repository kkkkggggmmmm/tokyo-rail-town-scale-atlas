# 東京圏 駅まちスケール・アトラス

東京圏の駅を入口に、駅へ接続する **commercial center（商業中心地）** の規模・タイプ・交通力・推定信頼度を分離して推定するプロジェクトです。

## Current status: G3 normalization PASS / G3.1 N03 boundary audit complete, use-determination gate blocked

Phase 0（正本定義・取得可能性監査）、G0/G1（公式ページ再確認・24アーカイブ原本ロック）、G2（station/group/hub/line identity）、G3（mesh/S12/L01正規化）を完了しました。G3.1では公式N03行政界の粒度・時点・許諾を再監査し、国土地理院の二次利用手続が必要か未確定であることを記録しました。そのためN03の取得、行政界clip、scope-aware mesh rollupは意図的に停止しています。最終ランキング、中心地の確定ポリゴン、公開UIは依然として作成していません。

- [Phase 0 audit report](docs/PHASE0_AUDIT_REPORT.md)
- [Source manifest](SOURCES.yml)
- [Data dictionary](DATA_DICTIONARY.md)
- [Center model](CENTER_MODEL.md)
- [Canonical schema](schema/canonical.sql)
- [Station-line crosswalk contract](schema/station_line_crosswalk.schema.yml)
- [Pilot scope](docs/PILOT_SCOPE.md)
- [Golden Eval registry](data/reference/GOLDEN_EVALS.yml)
- [Phase 1 execution plan](docs/PHASE1_EXECUTION_PLAN.md)
- [Phase 1 G0/G1 report](docs/PHASE1_G0_G1_REPORT.md)
- [Phase 1 acquisition scope](data/reference/PHASE1_ACQUISITION_SCOPE.yml)
- [Phase 1 source lock](data/manifests/source_lock.phase1.yml)
- [Official page hash recheck](data/manifests/official_recheck.phase1.yml)
- [Official correction/distribution recheck — 2026-08-30](docs/OFFICIAL_CORRECTION_RECHECK_2026-08-30.md)
- [Official recheck — 2026-09-05](docs/OFFICIAL_RECHECK_2026-09-05.md)
- [Phase 1 identity rules](data/reference/PHASE1_IDENTITY_RULES.yml)
- [Phase 1 G2 adjudications](data/reference/PHASE1_G2_ADJUDICATIONS.yml)
- [Phase 1 identity registry](data/reference/PHASE1_IDENTITY_REGISTRY.yml)
- [Phase 1 G2 identity report](docs/PHASE1_G2_IDENTITY_REPORT.md)
- [Phase 1 identity manifest](data/manifests/identity.phase1.yml)
- [Phase 1 G3 normalization report](docs/PHASE1_G3_NORMALIZATION_REPORT.md)
- [Phase 1 G3.1 boundary audit and stop gate](docs/PHASE1_G3_1_BOUNDARY_AUDIT.md)
- [G3.1 boundary source audit](data/reference/G3_1_BOUNDARY_SOURCE_AUDIT.yml)
- [G3.1 scope-rollup contract](data/reference/G3_1_SCOPE_ROLLUP_CONTRACT.yml)

## Canonical principles

1. 表示入口は駅、計算正本は `center`。
2. `Scale`、`Type`、`Access`、`Confidence` を別々に保持する。
3. 乗降客数は `Access` にのみ使い、街の規模の直接代理にしない。
4. 固定半径は診断用ベースラインに限り、最終境界には使わない。
5. 欠損・秘匿・非公開・対象外・観測0を区別する。
6. 各観測値に基準時点、公開時点、取得時点、source releaseを保持する。
7. Coreは1都3県全域で比較可能な公的統計に限定する。

## Repository layout

```text
.
├── AGENTS.md
├── PROJECT_STATE.md
├── DATA_DICTIONARY.md
├── SOURCES.yml
├── CENTER_MODEL.md
├── decisions/
├── docs/
├── schema/
├── data/reference/
├── tests/
└── scripts/
```

## Validation

```bash
make verify-fast
```

`verify-fast` is the clone-safe check run by GitHub Actions. It validates the required files, 8 pilot lines, 60 Golden Eval candidates, source-year separation, null semantics, canonical table declarations, the missingness fixtures, and the execution contract itself.

With the exact G1 raw archives mounted under `data/raw/phase1/`, additionally run:

```bash
make verify-locked
```

`verify-locked` validates the 24 raw archive bytes, ZIP members, source-lock hashes, and G2 opaque-ID/hub/exact-segment invariants. Raw archives are intentionally not committed to Git.

After G3 normalization has regenerated the local derivatives, run:

```bash
make verify-g3
```

It verifies mesh-partition identity, missingness, and the Access/validation domain
boundaries while keeping administrative-boundary clip and whole-mesh rollup blocked.

The license/use preflight can be checked separately with:

```bash
make verify-g3-1
```

It validates that N03 is still blocked until the intended secondary use has an
official determination. It does not download or process N03.
