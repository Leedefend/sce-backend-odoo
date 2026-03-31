# ITER-2026-03-30-337

## Summary

Pulled `workspace.home` back onto the usability productization mainline by
removing technical filter/result panels from the normal user-facing home view
and aligning section copy with product-facing workbench wording.

## Changed Files

- `frontend/apps/web/src/views/HomeView.vue`
- `agent_ops/tasks/ITER-2026-03-30-337.yaml`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-337.yaml` PASS
- `pnpm -C frontend/apps/web typecheck:strict` PASS

## User-Visible Result

- Normal users no longer see the `filters / result_summary / active_filters`
  technical panel on `workspace.home`.
- Home section fallback copy now reads in product terms:
  - `系统提醒`
  - `项目总体状态`
  - `补充提醒`
  - `常用功能`
- HUD mode still keeps the filter dataset available for debug-oriented checks.

## Risk Summary

- Frontend-only cleanup in `HomeView.vue`
- No backend contract changes
- No route, permission, or action handler changes

## Rollback

```bash
git restore agent_ops/tasks/ITER-2026-03-30-337.yaml
git restore frontend/apps/web/src/views/HomeView.vue
git restore agent_ops/reports/2026-03-30/report.ITER-2026-03-30-337.md
git restore agent_ops/state/task_results/ITER-2026-03-30-337.json
```

## Next Suggestion

Continue the usability productization mainline on `workspace.home` by trimming
remaining capability-browser weight in the lower half of the page and turning
the common entry area into a smaller, more explicit action deck.
