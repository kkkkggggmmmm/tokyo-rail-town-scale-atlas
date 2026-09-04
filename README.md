# 東京圏 駅まちスケール・アトラス

東京圏の駅を入口に、駅へ接続する **commercial center（商業中心地）** の規模・タイプ・交通力・推定信頼度を分離して推定するプロジェクトです。

## Current status: R0 canonical reset complete / Phase 1 G2 PASS / G3 ready

Phase 0（正本定義・取得可能性監査）、G0/G1（公式ページ再確認・24アーカイブ原本ロック）、G2（station/group/hub/line identity）を完了しました。2026-09-04にGitHub `main@5c886415` を再開基準として固定し、cloneだけで検証可能なCIと、raw archiveが必要な完全検証を分離しました。G3のmesh/S12/L01正規化が次の実装ゲートです。最終ランキング、中心地の確定ポリゴン、公開UIは依然として作成していません。

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
- [Phase 1 identity rules](data/reference/PHASE1_IDENTITY_RULES.yml)
- [Phase 1 G2 adjudications](data/reference/PHASE1_G2_ADJUDICATIONS.yml)
- [Phase 1 identity registry](data/reference/PHASE1_IDENTITY_REGISTRY.yml)
- [Phase 1 G2 identity report](docs/PHASE1_G2_IDENTITY_REPORT.md)
- [Phase 1 identity manifest](data/manifests/identity.phase1.yml)

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
