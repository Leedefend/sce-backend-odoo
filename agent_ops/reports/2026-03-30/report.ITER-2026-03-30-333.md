# ITER-2026-03-30-333

## Summary

Added a frontend-side recovery batch for list scenes that were still rendering
with fallback toolbar groups after the backend shipped
`optimization_composition`.

The batch now does two things:

- resolves `scene_ready_contract_v1` entries by `scene_key` first, then falls
  back to `action_id/menu_id/route` so action routes can still hit the correct
  scene-ready entry when the semantic scene key does not match the concrete list
  scene key
- keeps the one-shot `system.init` refresh guard for stale cached list scenes
  that still miss `optimization_composition`

## Changed Files

- `frontend/apps/web/src/app/resolvers/sceneReadyResolver.ts`
- `frontend/apps/web/src/views/ActionView.vue`
- `agent_ops/tasks/ITER-2026-03-30-333.yaml`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-333.yaml` PASS
- `pnpm -C frontend/apps/web typecheck:strict` PASS

## Runtime Result

- fixes scene-ready lookup on action routes where semantic scene identity and
  concrete list scene identity diverge
- narrows the refresh trigger to list action routes only
- requires existing list native truths before refreshing
- only refreshes once per page session
- preserves the existing fallback path if refreshed data still lacks
  `optimization_composition`

## Risk Summary

- Frontend-only additive batch
- No backend contract changes
- No contract field rename or removal
- No UI behavior changes when fresh scene-ready data is already present
- Low risk of repeated reload because the refresh is one-shot guarded
- Low risk of false scene-ready match because fallback uses explicit
  `action_id/menu_id/route` targets from the same backend contract

## Rollback

```bash
git restore agent_ops/tasks/ITER-2026-03-30-333.yaml
git restore frontend/apps/web/src/app/resolvers/sceneReadyResolver.ts
git restore frontend/apps/web/src/views/ActionView.vue
git restore agent_ops/reports/2026-03-30/report.ITER-2026-03-30-333.md
git restore agent_ops/state/task_results/ITER-2026-03-30-333.json
```

## Next Suggestion

Hard-refresh the list page on `5174` and verify that the toolbar switches from
fallback groups to backend-driven sections. If it does, the next low-risk batch
can trim now-obsolete fallback heuristics in `PageToolbar`.
