# Release Execution Protocol v1

## Scope
- Standardize release action execution for:
  - `promote_snapshot`
  - `approve_action`
  - `rollback_snapshot`

## Surface
- `sc.release.action.execution_protocol_version`
- `sc.release.action.execution_trace_json`
- audit trail release action entries now include execution trace

## Gate
- `verify.release.execution_protocol_guard`
- `verify.release.execution_trace_guard`
- `verify.release.execution_protocol.v1`

## Acceptance
- Every succeeded release action has a persisted execution trace.
- Audit trail can read the same trace without reconstructing runtime state.
- Promote / rollback follow the same protocol version and step language.
