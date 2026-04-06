# Non-Auth Dormant Cleanup Guard Blockers (ITER-2026-04-05-1053)

## Scope

- `addons/smart_construction_core/controllers/execute_controller.py`
- `addons/smart_construction_core/controllers/frontend_api.py`
- `addons/smart_construction_core/controllers/portal_execute_button_controller.py`
- `addons/smart_construction_core/controllers/ui_contract_controller.py`
- `addons/smart_core/controllers/platform_execute_api.py`
- `addons/smart_core/controllers/platform_menu_api.py`
- `addons/smart_core/controllers/platform_portal_execute_api.py`
- `addons/smart_core/controllers/platform_ui_contract_api.py`
- `scripts/verify/controller_allowlist_policy.py`
- `scripts/verify/controller_delegate_guard.py`
- `scripts/verify/controller_allowlist_routes_guard.py`
- `scripts/verify/controller_route_policy_guard.py`
- `Makefile`

## Findings

1. **Route parity exists (functional owner is in `smart_core`)**
   - `/api/execute_button` exists in `platform_execute_api.py`.
   - `/api/menu/tree` and `/api/user_menus` exist in `platform_menu_api.py`.
   - `/api/contract/portal_execute_button` and `/api/portal/execute_button` exist in `platform_portal_execute_api.py`.
   - `/api/ui/contract` exists in `platform_ui_contract_api.py`.

2. **Verification guard still binds to legacy filenames under `smart_construction_core`**
   - `controller_allowlist_routes_guard.py` and `controller_route_policy_guard.py` both read `CONTROLLER_ROUTE_POLICY` and resolve files under `addons/smart_construction_core/controllers`.
   - `CONTROLLER_ROUTE_POLICY` currently hard-codes `frontend_api.py` (plus other legacy files).
   - If legacy files are removed now, guard will fail with `missing allowlist controller file`.

3. **Current `verify.frontend_api` does not block cleanup by itself**
   - `verify.frontend_api` executes `scripts/verify/frontend_api_smoke.py` only.
   - But full controller boundary lane depends on `verify.controller.boundary.guard` (Makefile target), which still points to legacy allowlist inputs.

## Boundary Conclusion

- Dormant non-auth cleanup is **not yet executable as pure file deletion**.
- Primary blocker is **guard ownership coupling**, not runtime route ownership.
- Required precondition: migrate allowlist/policy ownership from legacy filenames to platform route-owner surfaces (or introduce compatibility mapping in guard scripts) before deleting legacy files.

## Risk Level

- `P1` governance risk (verification lane breakage).
- Runtime risk remains `low` because active route owners already exist in `smart_core`.

## Suggested Next Batch

- Open implement batch to refactor controller boundary guards so policy checks are source-of-truth on platform owners, then perform bounded dormant file cleanup in a follow-up verify batch.
