# Business Admin Config Role Entry Contract Runtime v1

## Scope
- Objective: deliver optional `role_entries` contract surface for config-center role-entry governance.
- Constraint: additive only; no ACL/menu definition semantic changes.

## Runtime Contract Shape
- Intent: `system.init`
- Surface: `data.role_entries`
- Shape:
  - `role_code`: string
  - `entries`: list
    - `entry_key`: string
    - `entry_type`: string
    - `is_enabled`: boolean
    - `sequence`: integer

## Verification Evidence
- PASS: `E2E_BASE_URL=http://localhost:8069 DB_NAME=sc_test python3 scripts/verify/native_business_admin_config_role_entry_intent_parity_verify.py`
- PASS: `E2E_BASE_URL=http://localhost:8069 DB_NAME=sc_test python3 scripts/verify/native_business_admin_config_role_entry_runtime_verify.py`
- PASS: `E2E_BASE_URL=http://localhost:8069 DB_NAME=sc_test python3 scripts/verify/native_business_admin_config_center_acceptance_pack.py`

## Notes
- `role_entries` is optional and non-breaking: absent payload keeps existing behavior.
- Current runtime verify ensures session-bootstrap-first flow and parity with `sc.dictionary(type=role_entry)` source.
