# ITER-2026-04-01-577

- status: PASS
- layer_target: Frontend Layer
- module: native list record-open affordance
- priority_lane: P1_core_usability
- changed_files:
  - frontend/apps/web/src/pages/ListPage.vue

## Summary of Change

- added a concise table-entry hint telling users that clicking a list row opens details
- kept the change local to `ListPage.vue`
- did not change row click behavior, routing, or data flow

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-577.yaml`: PASS
- `pnpm -C frontend/apps/web typecheck:strict`: PASS
- `make verify.portal.v0_5.container`: PASS

## Risk Analysis

- low risk
- display and guidance only
- no backend contract, action, or navigation behavior changes
- residual risk: save-return continuity remains an uncovered later mainline family

## Rollback Suggestion

- `git restore frontend/apps/web/src/pages/ListPage.vue`
- `git restore agent_ops/tasks/ITER-2026-04-01-577.yaml`

## Next Iteration Suggestion

- open a new P1 screen batch for the next native list mainline usability family after record-open affordance clarification
