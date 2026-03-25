# Release Operator Surface Model v1

## Goal

Provide a minimal release operator surface without changing released navigation semantics or bypassing release policy / orchestrator.

## Layer Target

- Platform Layer
- Delivery Runtime Layer
- Release Governance Layer
- Frontend Layer

## Module

- `addons/smart_core/delivery/release_operator_surface_service.py`
- `addons/smart_core/handlers/release_operator.py`
- `frontend/apps/web/src/views/ReleaseOperatorView.vue`

## Surface

The operator surface exposes:

- current release state
- pending approval actions
- promote candidates
- rollback entry
- release history

All mutations remain routed through:

- `ReleaseApprovalPolicyService`
- `ReleaseOrchestrator`
- `ReleaseAuditTrailService`

## Guarantees

- no direct frontend mutation against release models
- no bypass around release policy
- no bypass around release orchestrator
- all operator actions remain visible in audit trail
