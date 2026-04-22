# Non-Auth Dormant Cleanup Implement Task Pack (Proposed from ITER-2026-04-05-1053)

## Batch Goal

- Move controller-boundary guard policy ownership from legacy non-auth files in `smart_construction_core` to active platform owner surfaces in `smart_core`.
- Keep runtime behavior unchanged.
- Prepare safe deletion/archival of dormant legacy non-auth controller files in a dedicated follow-up batch.

## Layer Declaration

- Layer Target: Governance Implement (verify-chain alignment)
- Module: controller boundary guard scripts + policy map
- Module Ownership: platform governance scripts
- Kernel or Scenario: scenario
- Reason: current guard checks still enforce legacy file existence and block boundary cleanup.

## Allowed Change Scope (for next batch)

- `scripts/verify/controller_allowlist_policy.py`
- `scripts/verify/controller_allowlist_routes_guard.py`
- `scripts/verify/controller_route_policy_guard.py`
- `scripts/verify/controller_delegate_guard.py` (only if allowlist behavior must align)
- `docs/audit/boundary/*` (result docs)
- `agent_ops/tasks/**`, `agent_ops/reports/**`, `agent_ops/state/task_results/**`, `docs/ops/iterations/**`

## Out of Scope

- `security/**`, `record_rules/**`, `ir.model.access.csv`, `__manifest__.py`
- financial domains (`*payment*`, `*settlement*`, `*account*`)
- frontend functional behavior changes

## Implementation Steps

1. Add policy mapping for active platform owner files:
   - `platform_execute_api.py` → `/api/execute_button`
   - `platform_menu_api.py` → `/api/menu/tree`, `/api/user_menus`
   - `platform_portal_execute_api.py` → `/api/contract/portal_execute_button`, `/api/portal/execute_button`
   - `platform_ui_contract_api.py` → `/api/ui/contract`
2. Update guard scripts to resolve allowlist file paths against `addons/smart_core/controllers` for migrated entries.
3. Keep legacy-policy compatibility for unrelated entries until dedicated migration batch.
4. Run boundary and frontend verification gates.
5. If PASS, open a dedicated cleanup batch for deleting dormant legacy non-auth controller files.

## Acceptance Commands (next batch)

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-05-1054.yaml`
- `python3 -m py_compile scripts/verify/controller_allowlist_policy.py scripts/verify/controller_allowlist_routes_guard.py scripts/verify/controller_route_policy_guard.py scripts/verify/controller_delegate_guard.py`
- `make verify.controller.boundary.guard`
- `make verify.frontend_api`

## PASS Criteria

- Controller boundary guard passes without requiring dormant non-auth legacy files as policy source-of-truth.
- Frontend API smoke remains PASS.
- No forbidden paths touched.

## Rollback Suggestion

- `git restore scripts/verify/controller_allowlist_policy.py`
- `git restore scripts/verify/controller_allowlist_routes_guard.py`
- `git restore scripts/verify/controller_route_policy_guard.py`
- `git restore scripts/verify/controller_delegate_guard.py`

