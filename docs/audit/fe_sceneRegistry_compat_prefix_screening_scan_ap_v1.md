# FE SceneRegistry Compat Prefix Screening Scan AP v1

## Goal

Run a bounded scan around sceneRegistry compat prefix recognition before direct
implementation.

## Fixed Architecture Declaration

- Layer Target: Frontend governance scan
- Module: sceneRegistry compat prefix screening
- Module Ownership: frontend scene-first contract-consumer boundary
- Kernel or Scenario: scenario
- Reason: sceneRegistry compat prefix recognition is now the strongest residual
  private compat baseline, so the next low-cost step is to freeze its immediate
  dependency surface before implementation

## Scan Result

```json
[
  {
    "path": "frontend/apps/web/src/app/resolvers/sceneRegistry.ts",
    "module": "scene registry normalization",
    "feature": "compat prefix recognized as delivery route input",
    "reason": "normalizeDeliverySceneRoute still maps `/compat/action`, `/compat/form`, and `/compat/record` to `/s/<sceneKey>` through `NATIVE_UI_CONTRACT_ROUTE_PREFIXES`"
  },
  {
    "path": "frontend/apps/web/src/router/index.ts",
    "module": "router private compat registration",
    "feature": "compat route families still registered and guarded",
    "reason": "router still declares the three private compat route families, and sceneRegistry recognition remains adjacent to this guarded router baseline"
  },
  {
    "path": "frontend/apps/web/src/composables/useNavigationMenu.ts",
    "module": "native action normalization",
    "feature": "native-action normalization still falls back to compat path",
    "reason": "`/native/action/:id` normalization still rewrites unresolved cases to `/compat/action/:id`"
  },
  {
    "path": "frontend/apps/web/src/views/SceneView.vue",
    "module": "scene consumer",
    "feature": "scene route remains the preferred path after guarded normalization",
    "reason": "SceneView now prefers embedded scene query state, which means direct dependence on compat prefixes has already been reduced at the consumer layer"
  }
]
```

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-SCENEREGISTRY-COMPAT-PREFIX-SCREENING-SCAN-AP.yaml`
  - PASS
- bounded `rg` recheck across 4 declared frontend files
  - PASS
- `git diff --check -- agent_ops/tasks/ITER-2026-04-20-FE-SCENEREGISTRY-COMPAT-PREFIX-SCREENING-SCAN-AP.yaml docs/audit/fe_sceneRegistry_compat_prefix_screening_scan_ap_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md`
  - PASS

## Decision

- scan complete
- next eligible low-cost step is a screen that classifies whether sceneRegistry
  compat prefix recognition can now be isolated as the sole strong residual
  baseline before direct implementation
