# ITER-2026-03-30-280 Report

## Summary

- Surfaced native `searchpanel` metadata on list pages as read-only faceted hints.
- Extended the list scene-ready resolver to carry `searchpanel` facts through to the toolbar.
- Kept this batch display-only, without inventing click behavior before execution semantics exist.

## Changed Files

- `frontend/apps/web/src/app/resolvers/sceneReadyResolver.ts`
- `frontend/apps/web/src/views/ActionView.vue`
- `frontend/apps/web/src/pages/ListPage.vue`
- `frontend/apps/web/src/components/page/PageToolbar.vue`
- `agent_ops/tasks/ITER-2026-03-30-280.yaml`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-280.yaml`
- `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && pnpm -C frontend/apps/web typecheck:strict'`

## Risk

- Low
- Frontend-only and display-only.
- No backend contracts, routes, or search execution paths were changed.
- Searchpanel facts are shown as passive labels to avoid fake affordances.

## Rollback

```bash
git restore frontend/apps/web/src/app/resolvers/sceneReadyResolver.ts
git restore frontend/apps/web/src/views/ActionView.vue
git restore frontend/apps/web/src/pages/ListPage.vue
git restore frontend/apps/web/src/components/page/PageToolbar.vue
git restore agent_ops/tasks/ITER-2026-03-30-280.yaml
```

## Next Suggestion

- Continue the list-metadata line by deciding whether the next low-risk batch should target display refinement for searchpanel facets or limited execution support for a first safe facet.
