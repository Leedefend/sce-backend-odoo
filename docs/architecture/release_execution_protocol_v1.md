# Release Execution Protocol v1

## Goal
Freeze the execution layer for release actions so `promote / approve / rollback` no longer rely on ad hoc orchestrator branches.

## Layer Target
- L2: execution protocol engine
- L3: release orchestration runtime

## Contract
- protocol version: `release_execution_protocol_v1`
- action persistence:
  - `execution_protocol_version`
  - `execution_trace_json`

## Standard Steps
- `approver_gate`
- `approval_apply`
- `executor_gate`
- `approval_gate`
- `operation_execute`

## Runtime Rule
- `ReleaseOrchestrator` keeps policy/orchestration ownership.
- `ReleaseExecutionEngine` owns standard step execution and trace assembly.
- `sc.release.action` is the persistence anchor for execution trace.

## Compatibility
- No rollback of existing operator read/write/surface contracts.
- Execution trace is additive and exposed through audit/read layers.
