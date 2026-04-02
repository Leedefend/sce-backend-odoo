# ITER-2026-04-02-824

- status: PASS
- mode: screen
- layer_target: Backend Usability
- module: system.init startup minimal surface contract
- priority_lane: usability_verification_mainline
- risk: low

## Implementation Result

- `addons/smart_core/core/system_init_payload_builder.py`
  - startup minimal surface now preserves root-level:
    - `scene_channel`
    - `scene_channel_selector`
    - `scene_channel_source_ref`
    - `scene_contract_ref`

## Verification Result

- `make verify.portal.scene_channel_smoke.container`: PASS

## Decision

- PASS
- backend contract gap fixed without frontend specialization

## Next Iteration Suggestion

- rerun aggregate gate:
  - `make verify.portal.ui.v0_8.semantic.container`
