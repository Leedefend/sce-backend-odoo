# Phase 12 Stage 4: Payment Handoff Role Hints

## Scope

- Delivery-focused enhancement for `payment.request.available_actions`.
- No change to backend business state-machine behavior.
- Keep canonical envelope and execute intent contract unchanged.

## Changes

- Backend action surface now includes role handoff fields per semantic action:
  - `required_role_key`
  - `required_role_label`
  - `required_group_xmlid`
  - `handoff_hint`
- Frontend `ModelFormPage` renders role/handoff hints directly in semantic action cards.
- Handoff cross-stack smoke now asserts role hint fields exist and match expected roles:
  - `submit` / `done` -> `finance`
  - `approve` / `reject` -> `executive`

## Files

- `addons/smart_construction_core/handlers/payment_request_available_actions.py`
- `frontend/apps/web/src/api/paymentRequest.ts`
- `frontend/apps/web/src/pages/ModelFormPage.vue`
- `scripts/verify/payment_request_approval_handoff_smoke.py`
- `addons/smart_construction_core/tests/test_payment_request_available_actions_backend.py`
- `addons/smart_construction_core/tests/test_payment_request_action_surface_backend.py`

## Verification

- `make verify.frontend.typecheck.strict` ✅
- `make verify.frontend.build` ✅
- `make verify.portal.payment_request_approval_handoff_smoke.container DB_NAME=sc_demo` ✅
- `python3 -m py_compile addons/smart_construction_core/handlers/payment_request_available_actions.py scripts/verify/payment_request_approval_handoff_smoke.py` ✅

## Note

- `make test ... TEST_TAGS=sc_smoke,...` currently triggers unrelated baseline failures in shared smoke suites.
- This iteration uses focused build/typecheck + cross-stack smoke as delivery proof.
