# ITER-2026-04-02-833

- status: FAIL
- mode: implement
- layer_target: Backend Usability
- module: e2e login contract consumer compatibility
- risk: low

## Implementation Result

- updated token extraction compatibility in:
  - `scripts/e2e/e2e_scene_smoke.py`
  - `scripts/e2e/e2e_contract_smoke.py`
  - `scripts/verify/scene_admin_smoke.py`
- behavior: prefer `data.token`, fallback to `data.session.token`.

## Verification Result

- `make verify.e2e.scene`: PASS
- `make verify.e2e.scene_admin`: FAIL
- fail point: `scenes.export returned empty scenes`

## Decision

- FAIL
- stop condition triggered by failed acceptance command

## Next Iteration Suggestion

- recover scene_admin smoke for fallback runtime where export scenes may be empty.
