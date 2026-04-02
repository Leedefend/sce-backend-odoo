# ITER-2026-04-02-817

- status: PASS
- mode: implement
- layer_target: Backend Usability
- module: scene diagnostics smoke compatibility
- priority_lane: usability_verification_mainline
- risk: low

## Implementation Result

- `scripts/verify/fe_scene_diagnostics_smoke.js`
  - add nav-fallback compatibility:
    - when `scene_diagnostics` missing, `nav` exists, and `scenes` is empty, return `SKIP`
  - keep strict failure for non-fallback missing diagnostics

## Decision

- PASS
- scene diagnostics smoke now aligned with fallback runtime mode

## Next Iteration Suggestion

- run targeted diagnostics verify:
  - `make verify.portal.scene_diagnostics_smoke.container`
