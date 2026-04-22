# FE Post Public Compat Retirement Recheck Scan W v1

## Goal

Run a bounded recheck scan after public `/a /f /r` prefix retirement.

## Fixed Architecture Declaration

- Layer Target: Frontend governance scan
- Module: post-public compatibility retirement recheck
- Module Ownership: frontend scene-first contract-consumer boundary
- Kernel or Scenario: scenario
- Reason: public compatibility prefixes have already been retired, so the next
  low-cost step is to freeze what private compatibility surfaces still remain

## Scan Result

```json
[
  {
    "path": "frontend/apps/web/src/router/index.ts",
    "module": "router compatibility registration",
    "feature": "private compat prefixes with preserved route names",
    "reason": "router still registers `/compat/action/:actionId`, `/compat/form/:model/:id`, and `/compat/record/:model/:id` under route names `action`, `model-form`, and `record`"
  },
  {
    "path": "frontend/apps/web/src/app/resolvers/sceneRegistry.ts",
    "module": "scene registry route prefix recognition",
    "feature": "private compat prefix recognition",
    "reason": "native UI contract route prefixes still explicitly include `/compat/action/`, `/compat/form/`, and `/compat/record/`"
  },
  {
    "path": "frontend/apps/web/src/services/action_service.ts",
    "module": "generic action navigation builder",
    "feature": "private compat path dispatch",
    "reason": "generic action and record navigation still push to `/compat/action/...` and `/compat/record/...`"
  },
  {
    "path": "frontend/apps/web/src/views/SceneView.vue",
    "module": "scene-side navigation handoff",
    "feature": "private compat action fallback path",
    "reason": "scene-driven redirects still emit `/compat/action/...` when target resolution remains action-shaped"
  },
  {
    "path": "frontend/apps/web/src/composables/useNavigationMenu.ts",
    "module": "menu route normalization",
    "feature": "native-to-private compat rewrite",
    "reason": "menu route normalization still rewrites `/native/action/` to `/compat/action/`"
  },
  {
    "path": "frontend/apps/web/src/app/suggested_action/runtime.ts",
    "module": "suggested action runtime",
    "feature": "private compat path generation",
    "reason": "suggested-action parsing still materializes `/compat/action/...` and `/compat/record/...` links"
  },
  {
    "path": "frontend/apps/web/src/views/ActionView.vue, frontend/apps/web/src/pages/ContractFormPage.vue, frontend/apps/web/src/views/RecordView.vue, frontend/apps/web/src/components/view/ViewRelationalRenderer.vue",
    "module": "internal compatibility shells",
    "feature": "route-name-based compat handoff",
    "reason": "internal shells still navigate through route names `model-form` and `record`, which now land on private compat route registrations rather than public prefixes"
  }
]
```

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-POST-PUBLIC-COMPAT-RETIREMENT-RECHECK-SCAN-W.yaml`
  - PASS
- bounded `rg` recheck across 12 declared frontend files
  - PASS
- `git diff --check -- agent_ops/tasks/ITER-2026-04-20-FE-POST-PUBLIC-COMPAT-RETIREMENT-RECHECK-SCAN-W.yaml docs/audit/fe_post_public_compat_retirement_recheck_scan_w_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md`
  - PASS

## Decision

- scan complete
- next eligible low-cost step is a screen that classifies whether the remaining
  compatibility boundary should now be described as private compat infrastructure
  plus internal route-name shells only
