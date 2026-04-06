# auth_signup 1040 Reconciliation Note (ITER-2026-04-05-1043)

## Reconciled Batches

- implementation batch: `ITER-2026-04-05-1040` (`FAIL`)
- recovery screen: `ITER-2026-04-05-1041` (`PASS`)
- recovery implement: `ITER-2026-04-05-1042` (`PASS`)

## What Failed in 1040

- `scene_legacy_auth_smoke.py` command used wrong env variable (`FRONTEND_API_BASE_URL`).
- script actually binds base URL via `E2E_BASE_URL` / `ODOO_PORT`.

## Recovery Result

- command contract corrected in task pack:
  - from: `FRONTEND_API_BASE_URL=... python3 scripts/verify/scene_legacy_auth_smoke.py`
  - to: `E2E_BASE_URL=... python3 scripts/verify/scene_legacy_auth_smoke.py`
- rerun verification in `1042`:
  - `verify.frontend_api`: PASS
  - `scene_legacy_auth_smoke`: PASS

## Reconciliation Conclusion

- `1040` fail is classified as **verification contract mismatch**, not controller handoff logic defect.
- downstream batches should treat 1040 implementation delta as recovery-validated under corrected acceptance contract.

## Next Execution Baseline

- continue from post-Implement-1 state.
- use corrected smoke command contract for all subsequent auth-related acceptance batches.
