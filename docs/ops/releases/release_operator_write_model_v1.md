# Release Operator Write Model v1

## Scope

This batch governs the release operator write surface without reopening:

- FR-1 to FR-5
- released navigation
- Scene Asset v1
- Delivery Engine v1
- Edition Runtime Routing v1
- Edition Freeze Surface v1
- Release Approval Policy v1
- Release Operator Surface v1
- Release Operator Read Model v1

## Outcome

`promote / approve / rollback` are now routed through:

`intent -> release_operator_write_model_v1 -> ReleaseOrchestrator`

instead of entering the orchestrator as loosely structured params.

## Gate

- `make verify.release.operator_write_model_guard ...`
- `make verify.release.operator_write_model.v1 ...`
