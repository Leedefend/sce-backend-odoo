# ITER-2026-03-30-287 Report

## Summary

- Surfaced native searchpanel select semantics on the list toolbar.
- Facet dimensions now indicate whether they are single-select or multi-select based
  on existing Odoo metadata.
- Kept the batch passive and avoided introducing unsupported click behavior.

## Changed Files

- `frontend/apps/web/src/views/ActionView.vue`
- `agent_ops/tasks/ITER-2026-03-30-287.yaml`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-287.yaml`
- `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && pnpm -C frontend/apps/web typecheck:strict'`

## Risk

- Low
- Frontend-only and display-only.
- No execution semantics changed.
- Unknown `select` values still degrade safely to generic single-dimension wording.

## Rollback

```bash
git restore frontend/apps/web/src/views/ActionView.vue
git restore agent_ops/tasks/ITER-2026-03-30-287.yaml
```

## Next Suggestion

- Continue evaluating whether the first truly safe interactive facet should be based on an existing contract filter rather than raw searchpanel metadata.
