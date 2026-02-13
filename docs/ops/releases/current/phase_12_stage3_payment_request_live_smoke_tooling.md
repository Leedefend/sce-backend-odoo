# Phase 12 Stage 3: Payment Request Live Smoke Tooling

## Scope
- Strengthened `payment_request_approval_smoke.py` so it can validate a real record path instead of silently falling back to contract-only mode.
- Added smoke control switches:
  - `PAYMENT_REQUEST_SMOKE_AUTO_CREATE` (default `1`)
  - `PAYMENT_REQUEST_SMOKE_REQUIRE_LIVE` (default `0`)
  - `PAYMENT_REQUEST_SMOKE_REQUEST_RETRY_MAX` (default `60`)
  - `PAYMENT_REQUEST_SMOKE_REQUEST_RETRY_SLEEP_SEC` (default `2`)
- Added docs for the above in `docs/ops/verify/README.md`.

## Behavior Changes
- When no visible `payment.request` exists:
  - smoke now attempts to create a minimal `payment.request` using existing `api.data` contract.
- In live mode (`PAYMENT_REQUEST_SMOKE_REQUIRE_LIVE=1`):
  - smoke fails fast if it cannot enter the live-record path.
- In live path:
  - smoke now rejects `NOT_FOUND` for action intents (`available_actions`, `submit`, `execute.submit`, `approve`, `reject`, `done`).

## Verification
- Command:
  - `PAYMENT_REQUEST_SMOKE_REQUIRE_LIVE=1 make verify.portal.payment_request_approval_smoke.container DB_NAME=sc_demo`
- Result:
  - PASS
  - summary contains `auto_created=true`, `actions_count=4`, and no `NOT_FOUND` in live path.

## Notes
- This PR does not change business logic semantics for approval flow.
- `BUSINESS_RULE_FAILED` remains valid and expected for some actions in non-ready states.
