# Business Admin Config Role Entry Frontend Consumer v1

## Goal
- Consume runtime `role_entries` contract from `system.init` in frontend session layer.
- Keep fallback behavior unchanged when `role_entries` is absent.

## Implementation
- File: `frontend/apps/web/src/stores/session.ts`
- Added session contract types:
  - `RoleEntryContractRow`
  - `RoleEntryContractGroup`
- Added session state field:
  - `roleEntries: RoleEntryContractGroup[]`
- Added lifecycle handling:
  - restore from cache
  - clear/reset on logout and login reset
  - persist to local cache
  - parse from `system.init` payload `role_entries`

## Constraints Check
- No role hardcode added.
- No frontend permission patching.
- No ACL/backend authority changes.
- Fallback preserved (`roleEntries` defaults to empty list).

## Verification
- PASS `python3 scripts/verify/native_business_admin_config_role_entry_frontend_consumer_verify.py`
- PASS `E2E_BASE_URL=http://localhost:8069 DB_NAME=sc_test python3 scripts/verify/native_business_admin_config_role_entry_intent_parity_verify.py`
