# ITER-2026-04-02-820

- status: PASS
- mode: implement
- layer_target: Backend Usability
- module: scene governance action runtime
- priority_lane: usability_verification_mainline
- risk: low

## Implementation Result

- backend fixes:
  - `addons/smart_construction_scene/services/scene_governance_service.py`
    - `set_company_channel` now:
      - clears `sc.scene.rollback` / `sc.scene.use_pinned`
      - syncs current operator user-channel override with target channel
      - returns `rollback_active=false`
  - `addons/smart_core/handlers/scene_health.py`
    - when minimal `system.init` lacks channel diagnostics, recompute and backfill:
      - `scene_channel`
      - `scene_diagnostics.rollback_active`

## Verification Result

- `make verify.portal.scene_governance_action_smoke.container`: PASS

## Decision

- PASS
- scene governance action blocker recovered

## Next Iteration Suggestion

- rerun aggregate semantic gate:
  - `make verify.portal.ui.v0_8.semantic.container`
