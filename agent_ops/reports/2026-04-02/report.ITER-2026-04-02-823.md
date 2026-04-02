# ITER-2026-04-02-823

- status: FAIL
- mode: verify
- layer_target: Backend Usability
- module: semantic aggregate rerun verify
- priority_lane: usability_verification_mainline
- risk: low

## Verification Result

- `make verify.portal.ui.v0_8.semantic.container`: FAIL
- fail point: `verify.portal.scene_channel_smoke.container`
- error: `scene_channel missing`

## Decision

- FAIL
- stop condition triggered by failed `make verify.*`

## Next Iteration Suggestion

- create dedicated backend recovery batch:
  - recover root-level `scene_channel` and `scene_contract_ref` in app.init minimal startup surface
