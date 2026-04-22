# FE Router Compat Caller Migration Implement BQ v1

## verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-ROUTER-COMPAT-CALLER-MIGRATION-IMPLEMENT-BQ.yaml` → `PASS`
- `pnpm -C frontend/apps/web typecheck:strict` → `PASS`
- `pnpm -C frontend/apps/web build` → `PASS` with existing chunk-size warning only
- `git diff --check -- agent_ops/tasks/ITER-2026-04-20-FE-ROUTER-COMPAT-CALLER-MIGRATION-IMPLEMENT-BQ.yaml docs/verify/fe_router_compat_caller_migration_implement_bq_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md frontend/apps/web/src/views/RecordView.vue frontend/apps/web/src/views/ActionView.vue frontend/apps/web/src/pages/ContractFormPage.vue frontend/apps/web/src/components/view/ViewRelationalRenderer.vue` → `PASS`

## implementation

- the four real navigation callers now keep existing scene-first helper resolution
- when scene identity still cannot be resolved, they no longer fall back to `name: 'record'` or `name: 'model-form'`
- unresolved branches now route to diagnostic-only `workbench` with explicit `reason/diag/model/record_id/action_id/menu_id`

## decision

```json
{
  "status": "PASS",
  "real_navigation_dependency_on_compat_route_names": "removed_from_targeted_callers",
  "remaining_compat_dependency": "presentation-only or compatibility-entry surfaces only",
  "next_eligible_batch": "bounded recheck to determine whether router compat entry retirement is now eligible"
}
```
