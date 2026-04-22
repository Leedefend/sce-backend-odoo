# Non-Auth Dormant Cleanup Implementation Checkpoint (ITER-2026-04-05-1057)

## Implemented Cleanup

- deleted `addons/smart_construction_core/controllers/execute_controller.py`
- deleted `addons/smart_construction_core/controllers/frontend_api.py`
- deleted `addons/smart_construction_core/controllers/portal_execute_button_controller.py`
- deleted `addons/smart_construction_core/controllers/ui_contract_controller.py`

## Why Safe

- route ownership parity was previously verified (`ITER-2026-04-05-1052`).
- controller-boundary policy ownership was migrated to smart_core surfaces (`ITER-2026-04-05-1054`, reconciled by `ITER-2026-04-05-1056`).
- deleted files were dormant legacy route-definition surfaces and no longer import-wired in `smart_construction_core/controllers/__init__.py`.

## Verification

- `make verify.controller.boundary.guard` → PASS
- `docker exec sc-backend-odoo-prod-sim-odoo-1 sh -lc "FRONTEND_API_BASE_URL=http://localhost:8069 DB_NAME=sc_demo python3 /mnt/scripts/verify/frontend_api_smoke.py"` → PASS

## Risk Summary

- low-to-medium governance cleanup risk; no runtime regression detected in recovery acceptance path.
