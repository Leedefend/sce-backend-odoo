# smart_core Boundary Batch-B4 Legacy Group Sunset Plan

## Scope
- Module: `addons/smart_core/security/groups.xml`
- Goal: Freeze legacy `group_sc_*` as compatibility aliases only.

## Canonical Groups (Use These)
- `smart_core.group_smart_core_data_operator`
- `smart_core.group_smart_core_finance_approver`
- `smart_core.group_smart_core_scene_admin`

## Legacy Compat Groups (Do Not Use for New Code)
- `smart_core.group_sc_data_operator`
- `smart_core.group_sc_finance_approver`
- `smart_core.group_sc_scene_admin`

## Migration Rule
1. New handlers/services must reference `group_smart_core_*` only.
2. Existing `group_sc_*` are retained for runtime compatibility during migration window.
3. Cross-module references should be switched in batches and verified by compile + guard checks.

## Exit Criteria For Removing Legacy Groups
- No references to `smart_core.group_sc_*` in:
  - `addons/*`
  - `scripts/*`
  - tests and fixtures
- Security regression check passes in core flows.
- One full release cycle with canonical groups only.

## Current Status (Batch-B4)
- Canonical groups introduced and in active use.
- Legacy groups renamed with `Legacy Compat` and bridged through `implied_ids`.
- Core/owner/construction references migrated to canonical finance approver group.

## Rollback
- Revert Batch-B branch commits affecting:
  - `addons/smart_core/security/smart_core_security.xml`
  - `addons/smart_core/security/groups.xml`
  - cross-module group reference changes

