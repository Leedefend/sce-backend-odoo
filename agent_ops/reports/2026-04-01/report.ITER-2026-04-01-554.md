# ITER-2026-04-01-554

- status: PASS
- layer_target: Frontend Layer
- module: native metadata list toolbar consumer
- changed_files:
  - frontend/apps/web/src/components/page/PageToolbar.vue

## Summary of Change

- renamed both active-condition reset CTAs from `重置条件` to `清空全部条件`
- kept the existing reset handler and all clear behavior unchanged
- aligned the visible wording with the fact that multiple tracked conditions are cleared together

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-554.yaml`: PASS
- `pnpm -C frontend/apps/web typecheck:strict`: PASS

## Risk Analysis

- low risk
- display-only change
- no backend, contract, or interaction changes
- residual risk: a follow-up verify batch should confirm the clearer wording remains stable under the trusted smoke chain

## Rollback Suggestion

- `git restore frontend/apps/web/src/components/page/PageToolbar.vue`
- `git restore agent_ops/tasks/ITER-2026-04-01-554.yaml`

## Next Iteration Suggestion

- open a low-cost verify batch that confirms the reset-all wording cleanup remains display-only and keeps the verify chain green
