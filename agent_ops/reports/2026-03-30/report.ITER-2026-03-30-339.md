# ITER-2026-03-30-339

## Summary

Accelerated workbench productization by publishing more `workspace.home`
entries as pre-release usable functions whenever they already have a concrete
native route/action/record target, while keeping locked entries blocked.

## Changed Files

- `frontend/apps/web/src/views/HomeView.vue`
- `agent_ops/tasks/ITER-2026-03-30-339.yaml`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-339.yaml` PASS
- `pnpm -C frontend/apps/web typecheck:strict` PASS

## User-Visible Result

- `PREVIEW` entries with a concrete native target are now enterable from
  `workspace.home`.
- Their action label is now `预发布进入`, making the release state explicit.
- `LOCKED` entries remain blocked and still show disabled entry behavior.
- The compact home action deck now includes these pre-release-usable entries.

## Risk Summary

- Frontend-only entry gating change in `HomeView.vue`
- No backend contract changes
- No permission model changes

## Rollback

```bash
git restore agent_ops/tasks/ITER-2026-03-30-339.yaml
git restore frontend/apps/web/src/views/HomeView.vue
git restore agent_ops/reports/2026-03-30/report.ITER-2026-03-30-339.md
git restore agent_ops/state/task_results/ITER-2026-03-30-339.json
```

## Next Suggestion

Continue the same pre-release publication path by making the grouped home entry
surface show clearer state copy for native-backed preview entries, so users can
distinguish “可进入的预发布” from “尚未开放”. 
