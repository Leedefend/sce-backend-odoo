# ITER-2026-04-02-825

- status: FAIL
- mode: verify
- layer_target: Backend Usability
- module: semantic aggregate rerun verify
- risk: low

## Verification Result

- `make verify.portal.ui.v0_8.semantic.container`: FAIL
- fail point: `verify.portal.scene_rollback_smoke.container`
- error: `rollback_active=false`

## Decision

- FAIL
- stop condition triggered by failed `make verify.*`

## Next Iteration Suggestion

- create dedicated backend recovery batch for rollback diagnostics surface in app.init.
