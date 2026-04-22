# FE Compat Authority Retirement P v1

## Goal

Retire the remaining bounded frontend public compatibility authorities while
keeping the current internal compatibility shells in place.

## Fixed Architecture Declaration

- Layer Target: Frontend contract-consumer runtime
- Module: compatibility authority retirement
- Module Ownership: frontend scene-first entry authority
- Kernel or Scenario: scenario
- Reason: the latest screen isolated the remaining public compatibility
  authorities to router entry fallback plus ModelListPage, MenuView, and
  WorkbenchView

## Planned Change

- when scene identity cannot be derived, do not reopen `/a`
- redirect unresolved public compatibility entry traffic to workbench with
  explicit diagnostics instead
- keep `ActionView` / `ContractFormPage` / `RecordView` as internal
  compatibility shells for now

## Result

- `frontend/apps/web/src/router/index.ts`
  - menu-route fallback no longer returns public `action` route when scene
    identity is missing
  - direct `/a/:actionId` traffic now redirects to workbench with
    `CONTRACT_CONTEXT_MISSING` diagnostics when no scene can be derived
- `frontend/apps/web/src/pages/ModelListPage.vue`
  - legacy list route no longer reopens `action`; it now goes to workbench with
    explicit diagnostics when scene identity is unavailable
- `frontend/apps/web/src/views/MenuView.vue`
  - leaf and redirect unresolved action paths no longer reopen `action`; both
    now terminate at workbench diagnostic fallback
- `frontend/apps/web/src/views/WorkbenchView.vue`
  - unresolved menu target actions no longer push `/a/:actionId`; they now stay
    within workbench diagnostics
- internal compatibility shells were preserved:
  - `ActionView`
  - `ContractFormPage`
  - `RecordView`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-COMPAT-AUTHORITY-RETIREMENT-P.yaml`
  - PASS
- `pnpm -C frontend/apps/web typecheck:strict`
  - PASS
- `pnpm -C frontend/apps/web build`
  - PASS
  - note: existing chunk-size warning only
- `git diff --check -- agent_ops/tasks/ITER-2026-04-20-FE-COMPAT-AUTHORITY-RETIREMENT-P.yaml docs/verify/fe_compat_authority_retirement_p_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md frontend/apps/web/src/router/index.ts frontend/apps/web/src/pages/ModelListPage.vue frontend/apps/web/src/views/MenuView.vue frontend/apps/web/src/views/WorkbenchView.vue`
  - PASS

## Decision

- PASS
- the bounded public compatibility authority retirement target is complete for
  router entry fallback plus ModelListPage/MenuView/WorkbenchView
- route registrations still exist, but their ordinary unresolved public fallback
  authority has been further reduced
