# Business Admin Config Role Entry Frontend Filter v1

## Goal
- Apply generic navigation visibility filtering from runtime `role_entries` contract.
- Keep fallback-safe behavior when role mapping cannot be resolved.

## Implementation
- File: `frontend/apps/web/src/stores/session.ts`
- Runtime flow:
  1. Parse `role_entries` from `system.init` payload.
  2. Build `allowedKeys` from `__global__` and current role-code groups.
  3. Filter both `menuTree` and `releaseNavigationTree` with generic key matching.
  4. If no matched nodes, fallback to original navigation tree.

## Generic Match Surface
- Node direct/meta keys are considered:
  - `xmlid`
  - `menu_xmlid`
  - `action_xmlid`
  - `scene_key`
  - `model`
  - `key`
  - `menu_id`
  - `id`
  - `action_id`

## Constraints Check
- No role hardcode.
- No frontend permission patch.
- No backend ACL change.
- Fallback mandatory and preserved.

## Verification
- PASS `python3 scripts/verify/native_business_admin_config_role_entry_frontend_filter_verify.py`
- PASS `E2E_BASE_URL=http://localhost:8069 DB_NAME=sc_test python3 scripts/verify/native_business_admin_config_role_entry_intent_parity_verify.py`
