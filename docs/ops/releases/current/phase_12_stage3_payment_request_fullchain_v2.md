# Phase 12 Stage 3: Payment Request Fullchain v2

## Scope
- Kept existing side-effect intent envelope unchanged.
- Enhanced `payment.request.available_actions` contract for frontend auto-render:
  - `execute_intent`
  - `execute_params`
  - `idempotency_required`
  - `requires_reason`
- Normalized unsupported semantic action response in `payment.request.execute`:
  - `reason_code=UNSUPPORTED_BUTTON_TYPE`
- Frontend `ModelFormPage` now consumes action surface for `payment.request`:
  - semantic action buttons are rendered from backend contract
  - execution path uses `payment.request.execute` (not business-rule logic in frontend)
  - reject action prompts reason before execute

## Files
- `addons/smart_construction_core/handlers/payment_request_available_actions.py`
- `addons/smart_construction_core/handlers/payment_request_execute.py`
- `addons/smart_construction_core/tests/test_payment_request_action_surface_backend.py`
- `addons/smart_construction_core/tests/test_payment_request_available_actions_backend.py`
- `frontend/apps/web/src/api/paymentRequest.ts`
- `frontend/apps/web/src/pages/ModelFormPage.vue`
- `scripts/verify/payment_request_approval_smoke.py`

## Verification
- `make verify.frontend.typecheck.strict` ✅
- `make verify.frontend.build` ✅
- `make verify.portal.payment_request_approval_smoke.container DB_NAME=sc_demo` ✅
- `python3 -m py_compile ...payment_request_available_actions.py ...payment_request_execute.py ...payment_request_approval_smoke.py` ✅

## Notes
- Current smoke runs in contract-only path when demo finance user has no seeded payment request:
  - flow still passes with expected `NOT_FOUND`.
- This PR does not change business rule ownership:
  - backend remains source of truth
  - frontend only renders and triggers semantic intents.
