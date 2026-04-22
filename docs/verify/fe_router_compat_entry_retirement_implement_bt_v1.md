# FE Router Compat Entry Retirement Implement BT v1

## scope

- retire router `/compat/action` `/compat/form` `/compat/record` entries
- keep scope bounded to router registration only
- verify no remaining compile-time dependency survives

## verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-ROUTER-COMPAT-ENTRY-RETIREMENT-IMPLEMENT-BT.yaml` → `PASS`
- `pnpm -C frontend/apps/web typecheck:strict` → `PASS`
- `pnpm -C frontend/apps/web build` → `PASS` with existing chunk-size warning only
- `git diff --check -- agent_ops/tasks/ITER-2026-04-20-FE-ROUTER-COMPAT-ENTRY-RETIREMENT-IMPLEMENT-BT.yaml docs/verify/fe_router_compat_entry_retirement_implement_bt_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md frontend/apps/web/src/router/index.ts` → `PASS`

## implementation

- removed router registration for:
  - `/compat/action/:actionId`
  - `/compat/form/:model/:id`
  - `/compat/record/:model/:id`
- no scene-first or diagnostic routing logic was added elsewhere in this batch
- prior migration batches already removed real navigation and presentation-only dependencies, so retirement is now clean at router registration level

## decision

```json
{
  "status": "PASS",
  "router_compat_entry_registration": "retired",
  "scene_oriented_frontend_route_surface": "sole remaining primary route family",
  "remaining_compatibility_tail": "non-blocking references or dead compatibility metadata only",
  "topic_status": "substantially closed"
}
```
