# ITER-2026-03-30-282 Report

## Summary

- Surfaced native list search mode semantics on the toolbar.
- The list surface now distinguishes faceted search surfaces from plain search surfaces using existing metadata.
- Kept the enhancement passive and descriptive only.

## Changed Files

- `frontend/apps/web/src/app/resolvers/sceneReadyResolver.ts`
- `frontend/apps/web/src/views/ActionView.vue`
- `frontend/apps/web/src/pages/ListPage.vue`
- `frontend/apps/web/src/components/page/PageToolbar.vue`
- `agent_ops/tasks/ITER-2026-03-30-282.yaml`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-282.yaml`
- `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && pnpm -C frontend/apps/web typecheck:strict'`

## Risk

- Low
- Frontend-only and display-only.
- No search execution behavior was changed.
- Unknown search modes still fall back to raw mode text rather than failing.

## Rollback

```bash
git restore frontend/apps/web/src/app/resolvers/sceneReadyResolver.ts
git restore frontend/apps/web/src/views/ActionView.vue
git restore frontend/apps/web/src/pages/ListPage.vue
git restore frontend/apps/web/src/components/page/PageToolbar.vue
git restore agent_ops/tasks/ITER-2026-03-30-282.yaml
```

## Next Suggestion

- Continue the list metadata line by choosing between:
  - refining the passive searchpanel/search-mode presentation
  - or implementing a first narrow interactive facet flow with explicit execution semantics
