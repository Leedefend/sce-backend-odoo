# ITER-2026-04-01-571

- status: PASS
- layer_target: Frontend Layer
- module: primary-toolbar search visibility gating
- priority_lane: P1_core_usability
- changed_files:
  - frontend/apps/web/src/components/page/PageToolbar.vue

## Summary of Change

- gated the primary-toolbar search block with optimization composition's `search` section visibility instead of rendering it unconditionally
- aligned `showPrimaryToolbar` with the new `showSearchBlock` gate so toolbar visibility now reflects the same search/sort rendering semantics
- kept the change local to `PageToolbar.vue`

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-571.yaml`: PASS
- `pnpm -C frontend/apps/web typecheck:strict`: PASS
- `make verify.portal.v0_5.container`: PASS

## Risk Analysis

- medium risk but bounded
- frontend-only structural gating change
- no backend contract or interaction callback changes
- residual risk: sort-summary fallback semantics remain a separate follow-up and were not changed here

## Rollback Suggestion

- `git restore frontend/apps/web/src/components/page/PageToolbar.vue`
- `git restore agent_ops/tasks/ITER-2026-04-01-571.yaml`

## Next Iteration Suggestion

- open a new P1 screen batch for the next native list mainline usability family after search visibility alignment
