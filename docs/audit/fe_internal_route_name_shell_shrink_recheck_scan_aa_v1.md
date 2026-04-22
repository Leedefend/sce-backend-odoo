# FE Internal Route Name Shell Shrink Recheck Scan AA v1

## Goal

Run a bounded recheck scan after the internal route-name shell shrink batch.

## Fixed Architecture Declaration

- Layer Target: Frontend governance scan
- Module: internal route-name shell shrink recheck
- Module Ownership: frontend scene-first contract-consumer boundary
- Kernel or Scenario: scenario
- Reason: the latest batch moved bounded internal form/record navigation to
  scene-first, so the next low-cost step is to freeze what private compat
  surfaces still remain

## Scan Result

```json
[
  {
    "path": "frontend/apps/web/src/app/sceneNavigation.ts",
    "module": "scene-first shell navigation helper",
    "feature": "shared scene-first internal redirect",
    "reason": "bounded shells now use a shared helper to resolve scene-first form/record targets before any compat fallback is attempted"
  },
  {
    "path": "frontend/apps/web/src/views/ActionView.vue, frontend/apps/web/src/pages/ContractFormPage.vue, frontend/apps/web/src/views/RecordView.vue, frontend/apps/web/src/components/view/ViewRelationalRenderer.vue",
    "module": "internal route-name shells",
    "feature": "fallback-only model-form/record branches",
    "reason": "declared shells still contain `name: 'model-form'` and `name: 'record'`, but only behind `sceneLocation || ...` fallback branches rather than as preferred navigation"
  },
  {
    "path": "frontend/apps/web/src/router/index.ts, frontend/apps/web/src/app/resolvers/sceneRegistry.ts, frontend/apps/web/src/services/action_service.ts",
    "module": "private compat infrastructure",
    "feature": "private compat route registration and dispatch",
    "reason": "router registrations, scene registry prefix recognition, and generic action service dispatch still explicitly retain `/compat/action`, `/compat/form`, and `/compat/record`"
  }
]
```

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-INTERNAL-ROUTE-NAME-SHELL-SHRINK-RECHECK-SCAN-AA.yaml`
  - PASS
- bounded `rg` recheck across 8 declared frontend files
  - PASS
- `git diff --check -- agent_ops/tasks/ITER-2026-04-20-FE-INTERNAL-ROUTE-NAME-SHELL-SHRINK-RECHECK-SCAN-AA.yaml docs/audit/fe_internal_route_name_shell_shrink_recheck_scan_aa_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md`
  - PASS

## Decision

- scan complete
- next eligible low-cost step is a screen that classifies whether route-name
  shells are now fallback-only while private compat infrastructure remains the
  dominant residual boundary
