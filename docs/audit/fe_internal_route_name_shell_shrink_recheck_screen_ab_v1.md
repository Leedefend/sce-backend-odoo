# FE Internal Route Name Shell Shrink Recheck Screen AB v1

## Goal

Freeze the strongest bounded classification statement after the internal
route-name shell shrink recheck.

## Fixed Architecture Declaration

- Layer Target: Frontend governance screen
- Module: internal route-name shell shrink recheck
- Module Ownership: frontend scene-first contract-consumer boundary
- Kernel or Scenario: scenario
- Reason: the latest scan already froze the reduced residual set, so the next
  low-cost step is classification only

## Screen Result

- `next_candidate_family`
  - `private compat infrastructure as dominant residual boundary`

- `family_scope`
  - `private compat route registration, prefix recognition, and generic dispatch`
  - `frontend/apps/web/src/router/index.ts`
  - `frontend/apps/web/src/app/resolvers/sceneRegistry.ts`
  - `frontend/apps/web/src/services/action_service.ts`
  - `fallback-only internal route-name shells`
  - `frontend/apps/web/src/views/ActionView.vue`
  - `frontend/apps/web/src/pages/ContractFormPage.vue`
  - `frontend/apps/web/src/views/RecordView.vue`
  - `frontend/apps/web/src/components/view/ViewRelationalRenderer.vue`

- `reason`
  - internal `model-form` and `record` references still remain, but they now
    sit behind `sceneLocation || ...` fallback branches rather than preferred
    navigation
  - the remaining preferred-path compatibility surface is now concentrated more
    clearly in private `/compat/action`, `/compat/form`, `/compat/record`
    infrastructure
  - this screen does not surface a new backend semantic-supply blocker

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-INTERNAL-ROUTE-NAME-SHELL-SHRINK-RECHECK-SCREEN-AB.yaml`
  - PASS
- `git diff --check -- agent_ops/tasks/ITER-2026-04-20-FE-INTERNAL-ROUTE-NAME-SHELL-SHRINK-RECHECK-SCREEN-AB.yaml docs/audit/fe_internal_route_name_shell_shrink_recheck_screen_ab_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md`
  - PASS

## Decision

- screen complete
- strongest bounded statement after the latest shell shrink recheck:
  - route-name shells are no longer the dominant residual issue
  - private compat infrastructure is now the dominant remaining compatibility
    boundary
