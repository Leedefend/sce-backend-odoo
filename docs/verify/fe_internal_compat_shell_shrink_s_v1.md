# FE Internal Compat Shell Shrink S v1

## Goal

Shrink the remaining internal compatibility-shell `action` fallbacks in
RecordView and ContractFormPage.

## Fixed Architecture Declaration

- Layer Target: Frontend contract-consumer runtime
- Module: internal compatibility shell shrink
- Module Ownership: frontend scene-first entry authority
- Kernel or Scenario: scenario
- Reason: after the public authority retirement batches, the remaining
  `action` fallbacks are concentrated inside internal compatibility shells

## Planned Change

- keep explicit route registrations unchanged
- keep scene-first navigation when scene identity is available
- replace unresolved internal `action` fallbacks with workbench diagnostics

## Result

- `frontend/apps/web/src/views/RecordView.vue`
  - `pushSceneOrAction(...)` still prefers scene-first resolution, but no longer
    falls back to `name: 'action'` when scene identity is missing
  - unresolved cases now return to workbench diagnostics with
    `CONTRACT_CONTEXT_MISSING`
- `frontend/apps/web/src/pages/ContractFormPage.vue`
  - contract open actions with `actionId`
  - execute-button returned `nextActionId`
  - enterprise next-action navigation
  - saved filter navigation
  - all now go through one scene-first helper and no longer fall back directly
    to `name: 'action'` when scene identity is missing
- explicit route registrations remain unchanged in this batch

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-INTERNAL-COMPAT-SHELL-SHRINK-S.yaml`
  - PASS
- `pnpm -C frontend/apps/web typecheck:strict`
  - PASS
- `pnpm -C frontend/apps/web build`
  - PASS
  - note: existing chunk-size warning only
- `git diff --check -- agent_ops/tasks/ITER-2026-04-20-FE-INTERNAL-COMPAT-SHELL-SHRINK-S.yaml docs/verify/fe_internal_compat_shell_shrink_s_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md frontend/apps/web/src/views/RecordView.vue frontend/apps/web/src/pages/ContractFormPage.vue`
  - PASS

## Decision

- PASS
- the previously screened internal compatibility-shell `action` fallbacks in
  RecordView and ContractFormPage have been reduced
- the remaining compatibility route issue is now primarily about explicit route
  registrations rather than ordinary public fallback authority or internal shell
  reopen behavior
