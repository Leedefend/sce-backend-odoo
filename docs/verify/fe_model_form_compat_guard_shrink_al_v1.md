# FE Model Form Compat Guard Shrink AL v1

## Goal

Shrink the remaining `model-form` compat route baseline with a scene-first
router guard.

## Fixed Architecture Declaration

- Layer Target: Frontend contract-consumer runtime
- Module: model-form compat guard shrink
- Module Ownership: frontend scene-first contract-consumer boundary
- Kernel or Scenario: scenario
- Reason: `model-form` is still the only compat route family without a dedicated
  scene-first router guard

## Result

- `frontend/apps/web/src/router/index.ts`
  - added a dedicated `to.name === 'model-form'` guard
  - the guard now resolves scene-first from `scene_key`, `action_id`,
    `menu_id`, `model`, and positive `record_id`
  - when scene identity is available, `model-form` redirects to the scene path
    with `view_mode=form`
  - when scene identity cannot be resolved, the original `model-form` route is
    preserved as fallback and is not forced to workbench

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-MODEL-FORM-COMPAT-GUARD-SHRINK-AL.yaml`
  - PASS
- `pnpm -C frontend/apps/web typecheck:strict`
  - PASS
- `pnpm -C frontend/apps/web build`
  - PASS
  - note: existing chunk-size warning only
- `git diff --check -- agent_ops/tasks/ITER-2026-04-20-FE-MODEL-FORM-COMPAT-GUARD-SHRINK-AL.yaml docs/verify/fe_model_form_compat_guard_shrink_al_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md frontend/apps/web/src/router/index.ts`
  - PASS

## Decision

- PASS
- `model-form` compat route is no longer the only unguarded compat route family
- router-side private compat baseline has been further reduced while preserving
  fallback behavior for unresolved form opens
