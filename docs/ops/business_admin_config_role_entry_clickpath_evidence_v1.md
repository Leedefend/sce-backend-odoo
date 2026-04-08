# Business Admin Config Role Entry Clickpath Evidence v1

## Goal
- Provide runtime evidence that role-entry filtered navigation still exposes clickable targets.

## Verify Script
- `scripts/verify/native_business_admin_config_role_entry_clickpath_evidence_verify.py`

## Sampling Method
- Authenticate by role (`admin`, `pm`, `finance`, `outsider`, `outsider_controlled`).
- Call `system.init` with session bootstrap.
- Read `data.nav`, `data.role_entries`, `data.role_surface.role_code`.
- Apply same filter policy (global + current role group).
- Validate leaf nodes retain click targets (`action_id` or `menu_id`/`id` or route).
- `outsider_controlled` is created at runtime as a temporary user (`sc_role_profile=owner`) and deleted after verify.

## Current Runtime Evidence (sc_test)
- admin: clickable leaf count > 0
- pm: clickable leaf count > 0
- finance: clickable leaf count > 0
- outsider: no project/payment specific clickable entries detected
- outsider_controlled: no project/payment specific clickable entries detected

## Controlled Outsider Tightening Note
- Previous outsider evidence depended on historical sample account semantics.
- Current verify uses a controlled temporary outsider account to avoid sample drift noise.
- Scope is verify-only and does not change backend/ACL/frontend logic.

## Result
- PASS in current runtime sampling.
