# ITER-2026-04-02-827

- status: FAIL
- mode: verify
- layer_target: Backend Usability
- module: semantic aggregate rerun verify
- risk: low

## Verification Result

- `make verify.portal.ui.v0_8.semantic.container`: FAIL
- fail point: `verify.portal.scene_diagnostics_smoke.container`
- error: `scene_diagnostics.schema_version missing`

## Decision

- FAIL
- stop condition triggered by failed `make verify.*`

## Next Iteration Suggestion

- complete minimal diagnostics contract fields (`schema_version/scene_version/...`) and re-verify diagnostics + rollback.
