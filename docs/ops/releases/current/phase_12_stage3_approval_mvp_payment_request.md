# Phase 12 Stage 3: Approval MVP (Payment Request)

## Scope
- Added side-effect intents for payment request approval flow:
  - `payment.request.submit`
  - `payment.request.approve`
- Kept canonical envelope and idempotency contract shape consistent with existing intent patterns.
- Added finance scene for auto-rendered payment request approval list:
  - `finance.payment_requests`
- Added cross-stack smoke:
  - `make verify.portal.payment_request_approval_smoke.container`

## Contract Notes
- Side-effect intents now include:
  - `request_id`
  - `idempotency_key`
  - `idempotency_fingerprint`
  - replay evidence fields (`idempotent_replay`, `replay_from_audit_id`, etc.)
- Conflict behavior:
  - HTTP-like code `409`
  - `reason_code=IDEMPOTENCY_CONFLICT`

## Scene Orchestration
- New scene code: `finance.payment_requests`
- Scene target points to existing menu/action:
  - `smart_construction_core.menu_payment_request`
  - `smart_construction_core.action_payment_request_my`
- `system.init` role landing candidates and scene-key mapping updated for finance role.

## Verification Commands
- `make contract.catalog.export`
- `make contract.evidence.export`
- `make gate.contract`
- `make verify.portal.execute_button`
- `make verify.portal.bridge.e2e`
- `make verify.portal.payment_request_approval_smoke.container`
