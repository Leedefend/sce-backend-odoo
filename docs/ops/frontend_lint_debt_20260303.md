# Frontend Lint Debt Tracking (2026-03-03)

## Scope
- Package: `frontend/apps/web`
- Iteration lint command: `pnpm -C frontend/apps/web lint:src`

## Gate Baseline
- Stable gate uses:
  - `typecheck:strict`
  - `build`
- Make target: `make verify.frontend.quick.gate`

## Current Status
- Full lint and `lint:src` can still stall in this environment.
- Lint is tracked as non-blocking debt for delivery iterations.

## Follow-up Plan
1. Keep merge gate on `verify.frontend.quick.gate`.
2. Split lint into fast/slow lanes.
3. Burn down high-noise rule categories incrementally.
