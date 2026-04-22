# FE Model Form Compat Guard Shrink Recheck Scan AM v1

## Goal

Run a bounded recheck scan after model-form compat guard shrink.

## Fixed Architecture Declaration

- Layer Target: Frontend governance scan
- Module: model-form compat guard shrink recheck
- Module Ownership: frontend scene-first contract-consumer boundary
- Kernel or Scenario: scenario
- Reason: the latest batch added a scene-first guard for `model-form`, so the
  next low-cost step is to freeze what router-side compat baseline still remains

## Scan Result

```json
[
  {
    "path": "frontend/apps/web/src/router/index.ts",
    "module": "router private compat baseline",
    "feature": "all compat families now guarded scene-first",
    "reason": "router still registers `/compat/action`, `/compat/form`, and `/compat/record`, but `action`, `record`, and `model-form` all now have dedicated scene-first guard branches"
  },
  {
    "path": "frontend/apps/web/src/app/resolvers/sceneRegistry.ts",
    "module": "sceneRegistry compat prefix recognition",
    "feature": "compat prefix baseline still retained",
    "reason": "scene registry still explicitly recognizes `/compat/action/`, `/compat/form/`, and `/compat/record/` as scene-delivery input prefixes"
  }
]
```

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-MODEL-FORM-COMPAT-GUARD-SHRINK-RECHECK-SCAN-AM.yaml`
  - PASS
- bounded `rg` recheck across router and sceneRegistry
  - PASS
- `git diff --check -- agent_ops/tasks/ITER-2026-04-20-FE-MODEL-FORM-COMPAT-GUARD-SHRINK-RECHECK-SCAN-AM.yaml docs/audit/fe_model_form_compat_guard_shrink_recheck_scan_am_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md`
  - PASS

## Decision

- scan complete
- next eligible low-cost step is a screen that classifies whether the dominant
  residual private compat baseline has now narrowed mainly to sceneRegistry
  compat prefix recognition plus guarded router registration shell
