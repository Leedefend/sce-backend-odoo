# ITER-2026-04-01-529

- status: PASS
- layer_target: Verification Tooling
- module: MVP frontend smoke login compatibility
- changed_files:
  - scripts/verify/fe_mvp_list_smoke.js
  - scripts/verify/fe_mvp_write_smoke.js
  - Makefile

## Summary of Change

- aligned MVP frontend smoke login parsing with the current login contract by accepting `session.token || token`
- updated the v0.5 smoke entrypoints to default to the canonical smoke credentials instead of the known non-UI account
- aligned the MVP menu anchor with the current scene-based projects list contract
- updated the list smoke to resolve action model/view metadata from `head/views` when top-level fields are absent

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-529.yaml`: PASS
- `make verify.portal.v0_5.host`: PASS

## Risk Analysis

- low risk
- verify-tooling only
- no product code or backend contract files changed in this batch
- residual risk: run the resumed product verify batch on the trusted container lane before treating the usability line as fully verified

## Rollback Suggestion

- `git restore scripts/verify/fe_mvp_list_smoke.js`
- `git restore scripts/verify/fe_mvp_write_smoke.js`
- `git restore Makefile`
- `git restore agent_ops/tasks/ITER-2026-04-01-529.yaml`

## Next Iteration Suggestion

- reopen the native list toolbar verify batch on the trusted container lane and confirm the route-preset dedup change remains display-only
