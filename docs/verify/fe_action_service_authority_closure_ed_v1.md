# FE Action Service Authority Closure ED

- Scope:
  - `frontend/apps/web/src/services/action_service.ts`
- Change:
  - `openAction` still prefers `resolveSceneFirstActionLocation`
  - if no legal scene target can be derived, fallback no longer emits `/compat/action/...`; it now enters `workbench` with `CONTRACT_CONTEXT_MISSING` diagnostics
  - `openForm` still prefers `resolveSceneFirstFormOrRecordLocation`
  - if no legal scene target can be derived, fallback no longer emits `/r/...`; it now enters `workbench` with `CONTRACT_CONTEXT_MISSING` diagnostics and carries `model/record_id`
- Verification:
  - `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-21-FE-ACTION-SERVICE-AUTHORITY-CLOSURE-ED.yaml`
  - `pnpm -C frontend/apps/web typecheck:strict`
  - `pnpm -C frontend/apps/web build`
  - `git diff --check -- agent_ops/tasks/ITER-2026-04-21-FE-ACTION-SERVICE-AUTHORITY-CLOSURE-ED.yaml frontend/apps/web/src/services/action_service.ts docs/verify/fe_action_service_authority_closure_ed_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md`
