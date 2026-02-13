# Phase 12 Stage 3: Approval Live-Path Hardening v2

## Objective
- Increase delivery-grade reliability of payment request approval smoke and action-surface UX.
- Keep backend contract envelope stable and avoid workflow rule changes.

## Changes

### Verify / Cross-stack smoke
- `scripts/verify/payment_request_approval_smoke.py`
  - Selects target payment request by probing `payment.request.available_actions` first.
  - Prefers records with executable actions instead of state-only heuristics.
  - Auto-create path now adds an attachment for generated payment requests.
  - Semantic execute step prefers `primary_action_key` when available.
  - Summary now includes:
    - `primary_action_key`
    - `allowed_actions`
    - `blocked_reason_summary`

### Backend action surface
- `payment.request.available_actions` now exposes:
  - `allowed_by_state`
  - `allowed_by_method`
  - `allowed_by_precheck`

### Frontend form UX
- Semantic action hints now render `suggested_action`.
- Tooltip includes suggested action when action is blocked.

## Tests / Docs
- Backend tests updated to assert action allow-check dimensions.
- Verify documentation updated with action-surface-aware live-path behavior.
