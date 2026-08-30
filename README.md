# 東京圏 駅まちスケール・アトラス

東京圏の駅を入口に、駅へ接続する **commercial center（商業中心地）** の規模・タイプ・交通力・推定信頼度を分離して推定するプロジェクトです。

## Phase 0 status

Phase 0（正本定義・取得可能性監査）を完了し、正本リポジトリは [GitHub](https://github.com/kkkkggggmmmm/tokyo-rail-town-scale-atlas) の `main` です。現時点では最終ランキング、中心地の確定ポリゴン、公開UIを作成していません。

- [Phase 0 audit report](docs/PHASE0_AUDIT_REPORT.md)
- [Source manifest](SOURCES.yml)
- [Data dictionary](DATA_DICTIONARY.md)
- [Center model](CENTER_MODEL.md)
- [Canonical schema](schema/canonical.sql)
- [Station-line crosswalk contract](schema/station_line_crosswalk.schema.yml)
- [Pilot scope](docs/PILOT_SCOPE.md)
- [Golden Eval registry](data/reference/GOLDEN_EVALS.yml)
- [Phase 1 execution plan](docs/PHASE1_EXECUTION_PLAN.md)
- [Official correction/distribution recheck — 2026-08-30](docs/OFFICIAL_CORRECTION_RECHECK_2026-08-30.md)

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
```

The validator checks the required files, 8 pilot lines, 60 Golden Eval candidates, source-year separation, null semantics, and canonical table declarations.
