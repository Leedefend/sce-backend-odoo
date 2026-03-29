## Summary

- audited the current list consumer chain starting from `ActionView.vue`, `useActionPageModel.ts`, and `ListPage.vue`
- confirmed the current blocker is not missing backend list metadata, but an over-heavy frontend shell around an already capable list core
- established the next shortest implementation path: keep the existing `ListPage` core and trim the extra `ActionView` contract blocks for list routes

## Findings

- frontend already consumes a broad list contract surface:
  - title / subtitle / status / record count
  - columns + column labels
  - search / sort / filter
  - pagination
  - summary strip
  - grouped rows / group paging / group summary
  - primary create action
  - row click into detail
  - batch selection / archive / activate / delete / assign / export
- the list core is already implemented in [ListPage.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/pages/ListPage.vue)
- the heavy feeling comes from [ActionView.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/views/ActionView.vue), which still renders many generic pre-list blocks:
  - route preset
  - focus strip
  - strict alert
  - quick filters
  - saved filters
  - group by
  - quick actions
- [useActionPageModel.ts](/mnt/e/sc-backend-odoo/frontend/apps/web/src/app/assemblers/action/useActionPageModel.ts) confirms these sections are assembled as a generic action page VM, not because the backend lacks list basics

## Conclusion

- backend basic list metadata is already sufficient for a fast-delivery list path
- the next list implementation batch should not ask for more backend metadata first
- the shortest path is to keep the existing `ListPage` and reduce/suppress non-essential pre-table blocks on list routes, starting with `project.project`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-219.yaml`

## Risk

- low-risk audit batch
- no code-path changes

## Rollback

- run the `git restore ...` command listed in `agent_ops/tasks/ITER-2026-03-29-219.yaml`

## Next Suggestion

- implement a low-risk `project.project` list-shell batch that keeps `ListPage` but hides or compacts the generic `ActionView` pre-list blocks so the page reads like an Odoo-native list first
