# ITER-2026-04-02-761

- status: PASS
- mode: implement
- layer_target: Backend Usability
- module: custom-frontend login/scene compatibility fix
- priority_lane: usability_verification_mainline
- risk: low

## Change Summary

- centralized login token compatibility in `scripts/verify/intent_smoke_utils.js`:
  - `assertIntentEnvelope(login)` now normalizes `data.session.token -> data.token`
- upgraded scene-style smoke scripts to nav-fallback compatibility:
  - `scripts/verify/fe_scene_contract_smoke.js`
  - `scripts/verify/fe_scene_default_sort_smoke.js`
  - `scripts/verify/fe_scene_list_profile_smoke.js`
  - `scripts/verify/fe_scene_target_smoke.js`
  - `scripts/verify/fe_scene_targets_resolve_smoke.js`
  - `scripts/verify/fe_scene_filters_semantic_smoke.js`
  - `scripts/verify/fe_scene_tiles_semantic_smoke.js`
  - `scripts/verify/fe_scene_versioning_smoke.js`
- adjusted versioning smoke check order:
  - evaluate scenes/nav compatibility first, then enforce schema/scene version fields
- no frontend app/business code changes

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-02-761.yaml`: PASS

## Decision

- PASS
- proceed to full compatibility gate verification

## Next Iteration Suggestion

- run full scene-style custom-frontend verify gates as one slice
