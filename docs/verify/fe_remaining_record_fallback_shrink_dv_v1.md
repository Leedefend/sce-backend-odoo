# FE Remaining Record Fallback Shrink DV

## Goal

Reduce remaining `/compat/record/...` output in the known high-visibility
frontend producers by switching their fallback to the restored standard
`/r/:model/:id` route while preserving scene-first navigation.

## Verification

1. `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-21-FE-REMAINING-RECORD-FALLBACK-SHRINK-DV.yaml`
   - PASS
2. `pnpm -C frontend/apps/web typecheck:strict`
   - PASS
3. `pnpm -C frontend/apps/web build`
   - PASS
   - Existing bundle-size warning only
4. `make frontend.restart`
   - PASS
   - Frontend ready at `http://127.0.0.1:5174/`
5. `git diff --check -- agent_ops/tasks/ITER-2026-04-21-FE-REMAINING-RECORD-FALLBACK-SHRINK-DV.yaml frontend/apps/web/src/views/HomeView.vue frontend/apps/web/src/views/MyWorkView.vue frontend/apps/web/src/views/WorkbenchView.vue frontend/apps/web/src/services/action_service.ts docs/verify/fe_remaining_record_fallback_shrink_dv_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md`
   - PASS

## Result

`HomeView.vue`, `MyWorkView.vue`, `WorkbenchView.vue`, and
`services/action_service.ts` now preserve scene-first record navigation as the
primary path, but when scene resolution still cannot derive a scene path they
fall back to the restored standard `/r/:model/:id` route instead of the private
`/compat/record/...` prefix. This further shrinks compat usage without removing
the bounded bridge.
