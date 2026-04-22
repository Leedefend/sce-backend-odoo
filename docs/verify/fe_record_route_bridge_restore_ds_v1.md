# FE Record Route Bridge Restore DS

## Goal

Restore a thin frontend route bridge so real record URLs such as
`/r/sc.legacy.financing.loan.fact/53?menu_id=405&action_id=599` no longer
collapse into a blank page.

## Verification

1. `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-21-FE-RECORD-ROUTE-BRIDGE-RESTORE-DS.yaml`
   - PASS
2. `pnpm -C frontend/apps/web typecheck:strict`
   - PASS
3. `pnpm -C frontend/apps/web build`
   - PASS
   - Existing bundle-size warning only
4. `make frontend.restart`
   - PASS
   - Frontend ready at `http://127.0.0.1:5174/`
5. `git diff --check -- agent_ops/tasks/ITER-2026-04-21-FE-RECORD-ROUTE-BRIDGE-RESTORE-DS.yaml frontend/apps/web/src/router/index.ts docs/verify/fe_record_route_bridge_restore_ds_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md`
   - PASS

## Result

`router/index.ts` now restores a bounded record-route bridge by registering
`/r/:model/:id`, `/f/:model/:id`, and `/compat/record/:model/:id` onto
`ModelFormPage`. This does not roll back scene-first architecture; it only
gives still-existing real record URLs a legal consumer entry while producer-side
migration remains open.
