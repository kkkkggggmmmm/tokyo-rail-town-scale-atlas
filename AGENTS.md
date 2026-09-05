# AGENTS.md

## Scope

These instructions apply to the entire repository.

## Canonical source order

1. Owner intent and frozen decisions in `PROJECT_STATE.md`
2. Accepted decisions in `decisions/DECISION_REGISTER.md`
3. `DATA_DICTIONARY.md`, `SOURCES.yml`, `CENTER_MODEL.md`, and `schema/canonical.sql`
4. Versioned transformation code and tests
5. Derived artifacts

When canonical sources conflict, stop and record the conflict before modifying data or model behavior.

## Frozen constraints

- Initial display domain: Tokyo, Kanagawa, Saitama, Chiba; analysis may extend into a documented buffer.
- Public entry unit: station; computational unit: commercial center.
- Scale, Type, Access, and Confidence remain separate outputs.
- Ridership must not directly determine CoreScale or its class.
- A fixed-radius station buffer must not become the canonical center boundary.
- Data reference date/year must not be collapsed into a synthetic “2026 value.”
- No unauthorized scraping of Google Maps, Tabelog, or comparable services.
- Core inputs must be region-wide and methodologically comparable.
- PLATEAU, POI, and human-flow data remain Enhanced until a recorded decision promotes them.
- Raw-source values are immutable. Manual changes live in an override/decision layer with reason and provenance.

## ID and missingness guardrails

- Never use mutable source station codes, names, coordinates, or slugs as canonical primary keys.
- Canonical IDs are opaque, minted once, and connected to source releases through alias tables.
- Never infer `0` from an absent row, blank field, suppression token, non-public code, or out-of-scope record.
- Preserve the raw token and an explicit `observation_status` before numeric casting.
- Split/merge events create lineage records; do not silently recycle an existing center ID.

## Write scope by phase

Phase 0 permits governance documents, schemas, source manifests, pilot scope, Golden Evals, and synthetic fixtures only. It prohibits final scores, final center polygons, rankings, and public UI.

Phase 1 may acquire the fixed pilot sources, build crosswalks, run candidate extraction methods, and produce review-only outputs. Publication remains blocked until `PROJECT_STATE.md` explicitly changes.

## Required checks before commit

Run the clone-safe validation on every change:

```bash
make verify-fast
```

`verify-fast` must remain runnable from a clean Git clone. It validates the
canonical contracts and synthetic missingness fixtures but intentionally does
not claim that external raw archives were verified.

When a change touches source acquisition, locked raw inputs, G2 identity, or a
later transformation that consumes those inputs, mount the exact locked raw
bundle and additionally run:

```bash
make verify-locked
```

Do not weaken or skip `verify-locked` because raw inputs are absent from Git;
they are deliberately external and must match the source-lock hashes.

For later phases, add tests that separately report:

- Primary outcome: Golden Eval agreement and boundary quality
- Safety constraints: no null-to-zero conversion, no ridership leakage into CoreScale, no duplicate center count per line
- Cost/latency: ETL runtime and artifact size

The repository CI runs only `verify-fast`. Full locked-input validation is a
required local or controlled-runner gate, not a best-effort CI check.

## STOP conditions

Stop rather than improvise when any of the following is true:

- source usage terms are unresolved;
- station/center identity cannot be normalized without an ambiguous merge;
- missing and zero cannot be distinguished;
- reference and publication dates are conflated;
- a non-comparable source is proposed for Core;
- a requested change exceeds the current phase or write scope.
