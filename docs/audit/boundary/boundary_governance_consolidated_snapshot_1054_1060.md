# Boundary Governance Consolidated Snapshot (ITER-1054 ~ ITER-1060)

## Scope

- range: `ITER-2026-04-05-1054` to `ITER-2026-04-05-1060`
- objective: recover failed verification, reconcile status, and complete bounded non-auth boundary cleanup.

## Batch Timeline

| iter | type | status | core outcome |
| --- | --- | --- | --- |
| 1054 | implement | FAIL | controller guard policy migrated to smart_core owners; host `verify.frontend_api` timeout |
| 1055 | recovery screen | PASS | timeout root cause isolated to host endpoint/runtime mismatch |
| 1056 | recovery verify | PASS | 1054 acceptance replay succeeded via container-local reachable endpoint |
| 1057 | implement | PASS | removed 4 dormant non-auth legacy route-definition controllers |
| 1058 | screen | PASS | residue classification after 1057 identified single-file candidate |
| 1059 | screen | PASS | proved `capability_matrix_controller.py` unreferenced and safe to delete |
| 1060 | implement | PASS | deleted `capability_matrix_controller.py` and revalidated guard/smoke |

## Reconciliation Summary

- historical record kept:
  - `1054` remains FAIL in original host verification context.
- governance reconciliation applied:
  - `1056` provides PASS replay evidence and marks `1054` as **reconciled-verified**.
- evidence anchor:
  - `docs/audit/boundary/iter_1054_reconciliation_note.md`

## Cleanup Outcomes

### Removed legacy non-auth route-definition surfaces (`1057`)

- `addons/smart_construction_core/controllers/execute_controller.py`
- `addons/smart_construction_core/controllers/frontend_api.py`
- `addons/smart_construction_core/controllers/portal_execute_button_controller.py`
- `addons/smart_construction_core/controllers/ui_contract_controller.py`

### Removed unreferenced stub residue (`1060`)

- `addons/smart_construction_core/controllers/capability_matrix_controller.py`

## Verification Baseline (Post-Cleanup)

- guard chain:
  - `make verify.controller.boundary.guard` → PASS (1056/1057/1060)
- runtime smoke (reachable path):
  - `docker exec sc-backend-odoo-prod-sim-odoo-1 sh -lc "FRONTEND_API_BASE_URL=http://localhost:8069 DB_NAME=sc_demo python3 /mnt/scripts/verify/frontend_api_smoke.py"` → PASS

## Risk Posture

- closed:
  - duplicate/dormant non-auth legacy route-definition surface risk.
  - controller boundary policy ownership mismatch risk.
- retained operational caveat:
  - host-mode `make verify.frontend_api` can still be unstable if default host endpoint does not match active runtime topology.

## Handoff Recommendation

- boundary cleanup chain is stable for this objective.
- next objective options:
  1. create consolidated architecture inventory refresh for current controller ownership map;
  2. move to next boundary lane (handler/registry/orchestration residue) with the same staged governance pattern.
