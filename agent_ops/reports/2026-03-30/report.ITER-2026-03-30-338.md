# ITER-2026-03-30-338

## Summary

Compressed the lower half of `workspace.home` from a large grouped capability
browser into a smaller common-action deck for normal users, while preserving
the broader grouped browsing surface in HUD/debug mode.

## Changed Files

- `frontend/apps/web/src/views/HomeView.vue`
- `agent_ops/tasks/ITER-2026-03-30-338.yaml`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-338.yaml` PASS
- `pnpm -C frontend/apps/web typecheck:strict` PASS

## User-Visible Result

- Normal users now see a compact lower-half action deck instead of the full
  grouped capability browser.
- The deck keeps a small set of ready entries and provides a clear
  `进入我的工作` path for the full entry space.
- HUD mode still retains the grouped scene browser for diagnosis and broader
  runtime inspection.

## Risk Summary

- Frontend-only `HomeView` presentation cleanup
- No backend contract changes
- No route or permission behavior changes

## Rollback

```bash
git restore agent_ops/tasks/ITER-2026-03-30-338.yaml
git restore frontend/apps/web/src/views/HomeView.vue
git restore agent_ops/reports/2026-03-30/report.ITER-2026-03-30-338.md
git restore agent_ops/state/task_results/ITER-2026-03-30-338.json
```

## Next Suggestion

Continue `workspace.home` productization by tightening the hero and middle-zone
copy rhythm so the first screen reads more like one continuous workbench flow
and less like stacked independent panels.
