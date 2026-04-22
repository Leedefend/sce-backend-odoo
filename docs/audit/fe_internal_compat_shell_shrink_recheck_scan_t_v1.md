# FE Internal Compat Shell Shrink Recheck Scan T v1

## Goal

Run a bounded recheck scan after the internal compatibility-shell shrink batch.

## Fixed Architecture Declaration

- Layer Target: Frontend governance scan
- Module: internal compatibility shell shrink recheck
- Module Ownership: frontend scene-first entry authority
- Kernel or Scenario: scenario
- Reason: the latest batch reduced internal shell `action` fallbacks, so the
  next low-cost step is to freeze what compatibility route forms still remain

## Scan Result

- `explicit compatibility route registrations still present`
  - `frontend/apps/web/src/router/index.ts`
  - explicit route registrations remain for `/a/:actionId`,
    `/f/:model/:id`, and `/r/:model/:id`
  - router still resolves these forms scene-first where possible, but the forms
    themselves remain visible at route-registration layer

- `prior internal-shell action fallbacks now reduced`
  - `frontend/apps/web/src/views/RecordView.vue`
  - no remaining `name: 'action'` fallback in the bounded helper path; unresolved
    navigation now returns to workbench diagnostics
  - `frontend/apps/web/src/pages/ContractFormPage.vue`
  - bounded helper-based flows (`open action`, execute-button `nextActionId`,
    enterprise next action, saved filter navigation) no longer reopen `action`
    directly when scene identity is missing

- `scene-first identity carry remains intact`
  - router, RecordView, ContractFormPage and other consumers still retain
    `scene_key` carry and `findSceneByEntryAuthority(...)` usage
  - the remaining compatibility shape is therefore much more about explicit
    route forms than unresolved fallback reopen behavior

- `residual compatibility signals outside this bounded line`
  - the scan still sees route-form presence and scene-carry handling across
    router and other consumers
  - within the bounded surfaces targeted by recent batches, no new public or
    internal `action` fallback hotspot emerged beyond explicit route
    registrations themselves

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-INTERNAL-COMPAT-SHELL-SHRINK-RECHECK-SCAN-T.yaml`
  - PASS
- bounded `rg` recheck across router/pages/views/layouts
  - PASS
- `git diff --check -- agent_ops/tasks/ITER-2026-04-20-FE-INTERNAL-COMPAT-SHELL-SHRINK-RECHECK-SCAN-T.yaml docs/audit/fe_internal_compat_shell_shrink_recheck_scan_t_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md`
  - PASS

## Decision

- scan complete
- next eligible low-cost step is a screen only if the team wants the strongest
  post-shrink classification statement frozen formally
