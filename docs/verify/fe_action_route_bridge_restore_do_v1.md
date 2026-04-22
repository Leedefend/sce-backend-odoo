# FE Action Route Bridge Restore DO

## Goal

Restore a thin frontend route bridge so real action URLs such as
`/a/584?menu_id=385` no longer collapse into a blank page.

## Verification

1. `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-21-FE-ACTION-ROUTE-BRIDGE-RESTORE-DO.yaml`
   - PASS
2. `pnpm -C frontend/apps/web typecheck:strict`
   - PASS
3. `pnpm -C frontend/apps/web build`
   - PASS
   - Existing bundle-size warning only
4. `make frontend.restart`
   - PASS
   - Frontend ready at `http://127.0.0.1:5174/`
5. `git diff --check -- agent_ops/tasks/ITER-2026-04-21-FE-ACTION-ROUTE-BRIDGE-RESTORE-DO.yaml frontend/apps/web/src/router/index.ts docs/verify/fe_action_route_bridge_restore_do_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md`
   - PASS

## Result

`router/index.ts` now restores a bounded action-route bridge by registering both
`/a/:actionId` and `/compat/action/:actionId` onto `ActionViewShell`. This does
not revert the scene-first architecture; it only gives still-existing real
action URLs a legal consumer entry while the producer-side migration remains
open.
