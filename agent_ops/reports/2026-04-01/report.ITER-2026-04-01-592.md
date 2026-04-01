# ITER-2026-04-01-592

- status: PASS
- mode: implement
- layer_target: Frontend Layer
- module: record-view HUD contract-status prominence
- priority_lane: P1_core_usability
- risk: low

## Summary of Change

- reordered HUD entries in `useActionViewHudEntriesRuntime.ts`
- moved contract-status signals (`契约动作数`、`契约限制数`、`契约可读`、`契约告警数`、`契约降级`) ahead of filter/group metadata
- preserved labels, values, and field coverage

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-592.yaml`: PASS

## Risk Analysis

- bounded frontend-only ordering change
- no HUD schema, behavior, or contract changes

## Rollback Suggestion

- restore `frontend/apps/web/src/app/action_runtime/useActionViewHudEntriesRuntime.ts`

## Next Iteration Suggestion

- run strict typecheck and dedicated HUD smoke in `ITER-2026-04-01-593`
