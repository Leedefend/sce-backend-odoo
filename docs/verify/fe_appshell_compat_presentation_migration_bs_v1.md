# FE AppShell Compat Presentation Migration BS v1

## scope

- migrate AppShell presentation-only logic off compat route names
- keep shell behavior semantically equivalent
- keep scope bounded to AppShell only

## verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-APPSHELL-COMPAT-PRESENTATION-MIGRATION-BS.yaml` → `PASS`
- `pnpm -C frontend/apps/web typecheck:strict` → `PASS`
- `pnpm -C frontend/apps/web build` → `PASS` with existing chunk-size warning only
- `git diff --check -- agent_ops/tasks/ITER-2026-04-20-FE-APPSHELL-COMPAT-PRESENTATION-MIGRATION-BS.yaml docs/verify/fe_appshell_compat_presentation_migration_bs_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md frontend/apps/web/src/layouts/AppShell.vue` → `PASS`

## implementation

- AppShell no longer uses `route.name === 'action'|'record'|'model-form'` as its primary presentation conditions
- worksurface compactness now follows scene/layout/query semantics instead:
  - `activeLayout.kind`
  - `route.query.action_id`
  - `route.query.record_id`
  - `routeSceneKey`
- breadcrumb, page title, and entry-source fallbacks now rely on query/layout semantics rather than compat route names

## decision

```json
{
  "status": "PASS",
  "presentation_only_compat_route_name_dependency": "removed",
  "remaining_blocker_before_compat_entry_retirement": "needs one final retirement recheck only",
  "next_eligible_batch": "router compat entry retirement implement or verify chain"
}
```
