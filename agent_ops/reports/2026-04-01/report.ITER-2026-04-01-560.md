# ITER-2026-04-01-560

- status: PASS
- layer_target: Frontend Layer
- module: primary toolbar visibility gating
- changed_files:
  - frontend/apps/web/src/components/page/PageToolbar.vue

## Summary of Change

- widened `showPrimaryToolbar` so optimization mode keeps the primary toolbar mounted when the sort block is still visible, even if the search section is hidden
- kept the change local to the visibility gate
- did not change sort behavior, optimization section ordering, or any callbacks

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-560.yaml`: PASS
- `pnpm -C frontend/apps/web typecheck:strict`: PASS
- `make verify.portal.v0_5.container`: PASS

## Risk Analysis

- medium risk but bounded
- local structural change only
- no backend, contract, or interaction behavior changes detected
- residual risk: future optimization compositions may still need a dedicated policy for other primary-toolbar sub-blocks, but the current sort-summary case is now covered

## Rollback Suggestion

- `git restore frontend/apps/web/src/components/page/PageToolbar.vue`
- `git restore agent_ops/tasks/ITER-2026-04-01-560.yaml`

## Next Iteration Suggestion

- close out this toolbar iteration segment and submit the current bounded frontend chain before opening a fresh scan
