# FE Record Producer Fallback Shrink DU

## Goal

Reduce private `/compat/record/...` output in the weakest remaining record URL
producer by switching its fallback to the restored standard `/r/:model/:id`
route while preserving scene-first navigation.

## Verification

1. `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-21-FE-RECORD-PRODUCER-FALLBACK-SHRINK-DU.yaml`
   - PASS
2. `pnpm -C frontend/apps/web typecheck:strict`
   - PASS
3. `pnpm -C frontend/apps/web build`
   - PASS
   - Existing bundle-size warning only
4. `make frontend.restart`
   - PASS
   - Frontend ready at `http://127.0.0.1:5174/`
5. `git diff --check -- agent_ops/tasks/ITER-2026-04-21-FE-RECORD-PRODUCER-FALLBACK-SHRINK-DU.yaml frontend/apps/web/src/app/suggested_action/runtime.ts docs/verify/fe_record_producer_fallback_shrink_du_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md`
   - PASS

## Result

`frontend/apps/web/src/app/suggested_action/runtime.ts` now keeps scene-first
resolution as the primary path for `open_project` and `open_record`, but when
scene resolution still cannot derive a scene path it falls back to the restored
standard `/r/:model/:id` route instead of the private `/compat/record/...`
prefix. This shrinks compat usage without removing the bounded bridge.
