# ITER-2026-03-30-285 Report

## Summary

- Deduplicated list toolbar metadata hints so searchable-field hints no longer repeat
  dimensions already represented by native searchpanel facets.
- Preserved searchpanel visibility as the stronger native faceted signal.

## Changed Files

- `frontend/apps/web/src/views/ActionView.vue`
- `agent_ops/tasks/ITER-2026-03-30-285.yaml`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-285.yaml`
- `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && pnpm -C frontend/apps/web typecheck:strict'`

## Risk

- Low
- Frontend-only and display-only.
- No execution semantics changed.
- Dedup uses both field keys and labels to reduce noisy repetition.

## Rollback

```bash
git restore frontend/apps/web/src/views/ActionView.vue
git restore agent_ops/tasks/ITER-2026-03-30-285.yaml
```

## Next Suggestion

- Reassess whether the next batch should remain passive metadata refinement or begin the first constrained interactive facet flow.
