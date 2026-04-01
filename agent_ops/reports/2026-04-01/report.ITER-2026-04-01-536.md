# ITER-2026-04-01-536

- status: PASS
- layer_target: Frontend Layer
- module: native metadata list toolbar consumer
- changed_files:
  - frontend/apps/web/src/components/page/PageToolbar.vue

## Summary of Change

- updated the active-condition summary so it no longer treats `原生默认排序` as an applied condition
- preserved sort visibility for non-default sort states by leaving all other sort sources unchanged
- kept sorting behavior, callbacks, and sort summary block unchanged

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-536.yaml`: PASS
- `pnpm -C frontend/apps/web typecheck:strict`: PASS

## Risk Analysis

- low risk
- display-only change
- no backend, contract, or interaction changes
- residual risk: a follow-up verify batch should confirm the active-condition summary now stays empty under native default sort while still surfacing non-default sort states

## Rollback Suggestion

- `git restore frontend/apps/web/src/components/page/PageToolbar.vue`
- `git restore agent_ops/tasks/ITER-2026-04-01-536.yaml`

## Next Iteration Suggestion

- open a low-cost verify batch that confirms the default-sort cleanup remains display-only and keeps the trusted toolbar smoke green
