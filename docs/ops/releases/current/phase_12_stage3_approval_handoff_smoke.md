# Phase 12 Stage 3: Payment Request Approval Handoff Smoke

## Goal
Add a delivery-oriented cross-role smoke for payment request approval handoff, without changing backend business behavior.

## Scope
- New verify script:
  - `scripts/verify/payment_request_approval_handoff_smoke.py`
- New make target:
  - `make verify.portal.payment_request_approval_handoff_smoke.container`
- Verify docs update:
  - `docs/ops/verify/README.md`

## Handoff Chain Covered
1. Finance login and candidate selection (`submit` allowed).
2. Finance executes `payment.request.execute` with `submit`.
3. Executive probes action surface and executes one allowed follow-up action (`approve` preferred, fallback `reject`).
4. Finance re-probes action surface and executes `done` only when allowed.

## Contract Expectations
- All side-effect steps use canonical intent envelope and reason code fields.
- No frontend business-rule branching is introduced.
- Script records evidence under:
  - `artifacts/codex/payment-request-approval-handoff-smoke/<timestamp>/`

## Verification
- `python3 -m py_compile scripts/verify/payment_request_approval_handoff_smoke.py`
- `make verify.portal.payment_request_approval_handoff_smoke.container DB_NAME=sc_demo`
- `make verify.portal.payment_request_approval_smoke.container DB_NAME=sc_demo`
