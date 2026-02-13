# Phase 12 Stage 3: Approval Delivery Polish v1

## Scope
- Keep existing payment request approval intent contract envelope stable.
- Improve business usability of `payment.request.available_actions` and form semantic action UX.
- No backend workflow rule changes.

## Backend
- `payment.request.available_actions` now returns per-action delivery hints:
  - `current_state`
  - `next_state_hint`
  - `blocked_message`
  - `suggested_action`
- Added list-level `primary_action_key` for auto-render emphasis.

## Frontend
- `ModelFormPage` renders semantic action transition hints and blocked reasons.
- Primary semantic action is visually highlighted based on `primary_action_key`.
- Added execution UX guardrails:
  - Confirm dialog for `approve` / `done`
  - Reject reason length check
- Action feedback now explains idempotent replay reuse.

## Verify
- Updated `payment_request_approval_smoke.py` to assert action-surface hint fields in live path.

## Notes
- This iteration is delivery-focused: it improves clarity and operation success rate without changing business state-machine semantics.
