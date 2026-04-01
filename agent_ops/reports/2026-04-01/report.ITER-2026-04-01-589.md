# ITER-2026-04-01-589

- status: PASS
- mode: implement
- layer_target: Frontend Layer
- module: record-view HUD key-signal ordering
- priority_lane: P1_core_usability
- risk: low

## Summary of Change

- reordered HUD entries in `useActionViewHudEntriesRuntime.ts`
- moved `当前排序`、`最近意图`、`写入模式`、`追踪 ID`、`耗时毫秒`、`当前路由` ahead of filter/group-window technical metadata
- preserved labels, values, and field coverage

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-589.yaml`: PASS

## Risk Analysis

- bounded frontend-only ordering change
- no HUD schema, behavior, or data-source changes

## Rollback Suggestion

- restore `frontend/apps/web/src/app/action_runtime/useActionViewHudEntriesRuntime.ts`

## Next Iteration Suggestion

- run strict typecheck and dedicated HUD smoke in `ITER-2026-04-01-590`
