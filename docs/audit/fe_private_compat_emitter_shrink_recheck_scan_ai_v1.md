# FE Private Compat Emitter Shrink Recheck Scan AI v1

## Goal

Run a bounded recheck scan after private compat emitter shrink.

## Fixed Architecture Declaration

- Layer Target: Frontend governance scan
- Module: private compat emitter shrink recheck
- Module Ownership: frontend scene-first contract-consumer boundary
- Kernel or Scenario: scenario
- Reason: the latest batch moved bounded entry surfaces to scene-first, so the
  next low-cost step is to freeze what private compat baseline still remains

## Scan Result

```json
[
  {
    "path": "frontend/apps/web/src/app/sceneNavigation.ts, frontend/apps/web/src/views/WorkbenchView.vue, frontend/apps/web/src/views/HomeView.vue, frontend/apps/web/src/views/MyWorkView.vue, frontend/apps/web/src/views/ProjectsIntakeView.vue",
    "module": "entry surfaces and shared helper",
    "feature": "scene-first preferred navigation with compat fallback only",
    "reason": "entry surfaces now use shared scene-first helpers and keep compat strings only behind fallback branches; ProjectsIntakeView no longer routes through /compat/form"
  },
  {
    "path": "frontend/apps/web/src/router/index.ts",
    "module": "private compat route registration",
    "feature": "private compat route baseline still registered",
    "reason": "router still declares `/compat/action/:actionId`, `/compat/form/:model/:id`, and `/compat/record/:model/:id`"
  },
  {
    "path": "frontend/apps/web/src/app/resolvers/sceneRegistry.ts",
    "module": "private compat prefix recognition",
    "feature": "compat prefix still recognized as scene delivery input",
    "reason": "scene registry still explicitly treats `/compat/action/`, `/compat/form/`, and `/compat/record/` as native UI contract route prefixes"
  }
]
```

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-PRIVATE-COMPAT-EMITTER-SHRINK-RECHECK-SCAN-AI.yaml`
  - PASS
- bounded `rg` recheck across 7 declared frontend files
  - PASS
- `git diff --check -- agent_ops/tasks/ITER-2026-04-20-FE-PRIVATE-COMPAT-EMITTER-SHRINK-RECHECK-SCAN-AI.yaml docs/audit/fe_private_compat_emitter_shrink_recheck_scan_ai_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md`
  - PASS

## Decision

- scan complete
- next eligible low-cost step is a screen that classifies whether router
  registration and sceneRegistry compat prefix recognition are now the dominant
  residual private compat baseline
