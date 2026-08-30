# 東京圏 駅まちスケール・アトラス

東京圏の駅を入口に、駅へ接続する **commercial center（商業中心地）** の規模・タイプ・交通力・推定信頼度を分離して推定するプロジェクトです。

## Current status: Phase 1 G2 candidate review

Phase 0（正本定義・取得可能性監査）とG0/G1（公式ページ再確認・24アーカイブ原本ロック）を完了し、G2の駅・駅群・hub・路線identity候補を生成しました。正本リポジトリは [GitHub](https://github.com/kkkkggggmmmm/tokyo-rail-town-scale-atlas) の `main` です。G2はレビュー中で、最終ランキング、中心地の確定ポリゴン、公開UIは作成していません。

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
- [Phase 1 identity registry](data/reference/PHASE1_IDENTITY_REGISTRY.yml)
- [Phase 1 identity candidate report](docs/PHASE1_G2_IDENTITY_REPORT.md)
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
python scripts/validate_phase0.py
python scripts/validate_phase1_lock.py
python scripts/validate_phase1_identity.py
```

The validators check the required files, 8 pilot lines, 60 Golden Eval candidates, source-year separation, null semantics, canonical table declarations, the local G1 byte/member lock, and G2 opaque-ID/crosswalk/review-queue invariants. Raw archives are intentionally not committed to Git.
