# Baseline Freeze Policy

## Purpose
- Freeze stabilized baseline paths to avoid repeated churn in `verify/gate` during high-velocity iterations.
- Shift iteration focus to business capability increments; baseline changes are limited to `P0` fixes.

## Freeze Scope
- Scene observability baseline scripts and aggregate commands.
- Directly coupled preflight/readiness diagnostic scripts.
- Related gate wiring (`gate.full` observability baseline coverage).

Notes:
- Machine-enforced scope is defined only by `scripts/verify/baselines/baseline_frozen_paths.json`.

## Allowed Changes
- `P0` incident fixes (blocking gate or causing false pass).
- Security/compliance fixes.
- Explicitly approved exception changes (must include rollback and evidence).

## Disallowed Changes
- Refactors without business necessity.
- Script behavior rewrites without evidence chain.
- Merging temporary troubleshooting logic into frozen baseline.

## Exception Flow
1. State exception reason and blast radius in PR description.
2. Provide rollback plan and verification commands.
3. Run guard with `BASELINE_FREEZE_ALLOW=1` for this exception only.

## Commands
- Baseline freeze guard:
  - `make verify.baseline.freeze_guard`
- Temporary exception run:
  - `BASELINE_FREEZE_ALLOW=1 make verify.baseline.freeze_guard`
