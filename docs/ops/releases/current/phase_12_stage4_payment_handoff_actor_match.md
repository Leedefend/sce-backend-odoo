# Phase 12 Stage 4: Payment Handoff Actor Match Contract

## Scope

- Keep payment approval business behavior unchanged.
- Extend action-surface contract so frontend can guide handoff by current actor role.

## Backend Contract Additions

Intent: `payment.request.available_actions`

Per action item now includes:

- `actor_matches_required_role: boolean`
- `handoff_required: boolean`

Existing fields remain unchanged:

- `required_role_key`
- `required_role_label`
- `required_group_xmlid`
- `handoff_hint`

## Frontend Delivery

- `ModelFormPage` renders actor-role match hint in semantic action cards.
- When role mismatch exists, UI shows explicit handoff copy:
  - `请转交给 <角色> 处理`

## Verification

- `make verify.frontend.typecheck.strict` ✅
- `make verify.frontend.build` ✅
- `make verify.portal.payment_request_approval_smoke.container DB_NAME=sc_demo` ✅
- `make verify.portal.payment_request_approval_handoff_smoke.container DB_NAME=sc_demo` ✅
