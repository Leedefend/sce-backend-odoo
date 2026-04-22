# FE Private Compat Infra Shrink Recheck Screen AF v1

## Goal

Freeze the strongest bounded classification statement after private compat
infrastructure shrink recheck.

## Fixed Architecture Declaration

- Layer Target: Frontend governance screen
- Module: private compat infrastructure shrink recheck
- Module Ownership: frontend scene-first contract-consumer boundary
- Kernel or Scenario: scenario
- Reason: the latest scan already froze the reduced residual set, so the next
  low-cost step is classification only

## Screen Result

- `next_candidate_family`
  - `router-and-registry private compat baseline`

- `family_scope`
  - `private compat route registration and prefix recognition`
  - `frontend/apps/web/src/router/index.ts`
  - `frontend/apps/web/src/app/resolvers/sceneRegistry.ts`
  - `secondary unresolved fallback emitters`
  - `frontend/apps/web/src/services/action_service.ts`
  - `frontend/apps/web/src/composables/useNavigationMenu.ts`
  - `frontend/apps/web/src/app/suggested_action/runtime.ts`

- `reason`
  - active compat dispatch sources now prefer scene-first and keep compat only as
    unresolved fallback
  - the most stable residual private compat boundary is now concentrated in
    router registration and sceneRegistry prefix recognition
  - this screen does not surface a new backend semantic-supply blocker

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-PRIVATE-COMPAT-INFRA-SHRINK-RECHECK-SCREEN-AF.yaml`
  - PASS
- `git diff --check -- agent_ops/tasks/ITER-2026-04-20-FE-PRIVATE-COMPAT-INFRA-SHRINK-RECHECK-SCREEN-AF.yaml docs/audit/fe_private_compat_infra_shrink_recheck_screen_af_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md`
  - PASS

## Decision

- screen complete
- strongest bounded statement after the latest private compat shrink recheck:
  - active dispatch is no longer the dominant residual issue
  - router registration and sceneRegistry compat prefix recognition are now the
    dominant remaining private compat baseline
