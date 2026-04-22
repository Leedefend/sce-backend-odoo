# FE Compat Authority Retirement Recheck Scan Q v1

## Goal

Run a bounded recheck scan after the public compatibility authority retirement
batch.

## Fixed Architecture Declaration

- Layer Target: Frontend governance scan
- Module: compatibility authority retirement recheck
- Module Ownership: frontend scene-first entry authority
- Kernel or Scenario: scenario
- Reason: the latest implement batch retired a set of public `/a` fallbacks, so
  the next low-cost step is to freeze what compatibility route forms still
  remain

## Scan Result

- `public compatibility route forms still present`
  - `frontend/apps/web/src/router/index.ts`
  - explicit route registrations still remain for `/a/:actionId`,
    `/f/:model/:id`, and `/r/:model/:id`
  - the router guard now prevents unresolved `/a/:actionId` traffic from acting
    as ordinary fallback authority by redirecting it to workbench diagnostics

- `prior public `/a` fallback targets are now cleared`
  - `frontend/apps/web/src/pages/ModelListPage.vue`
  - unresolved list-route cases no longer reopen `action`
  - `frontend/apps/web/src/views/MenuView.vue`
  - unresolved leaf/redirect menu cases no longer reopen `action`
  - `frontend/apps/web/src/views/WorkbenchView.vue`
  - unresolved menu-target cases no longer push `/a/${actionId}`

- `internal compatibility shells still retain `action` references`
  - `frontend/apps/web/src/views/RecordView.vue`
  - still contains `pushSceneOrAction(...)` fallback to `name: 'action'`
  - `frontend/apps/web/src/pages/ContractFormPage.vue`
  - still contains several `name: 'action'` fallbacks
  - these references now appear concentrated inside internal compatibility shells
    rather than the public authority surfaces targeted by batch P

- `scene-first identity carry remains active`
  - router, ModelListPage, MenuView, RecordView and related consumers still
    carry `scene_key` and continue to use `findSceneByEntryAuthority(...)`
  - the current recheck therefore shows contraction of public unresolved
    compatibility authority rather than wholesale removal of compatibility shell
    mechanics

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-COMPAT-AUTHORITY-RETIREMENT-RECHECK-SCAN-Q.yaml`
  - PASS
- bounded `rg` recheck across router/pages/views/layouts
  - PASS
- `git diff --check -- agent_ops/tasks/ITER-2026-04-20-FE-COMPAT-AUTHORITY-RETIREMENT-RECHECK-SCAN-Q.yaml docs/audit/fe_compat_authority_retirement_recheck_scan_q_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md`
  - PASS

## Decision

- scan complete
- next eligible low-cost step is a separate screen if the team wants a fresh
  post-retirement classification of the remaining compatibility route forms
