# v2 Execute Button Slice Spec v1

## Scope

This slice defines the fourth reusable v2 mainline pattern around `execute_button`.

Covered layers:

- intent registry reachability
- dispatcher execution closure
- schema validation execution
- handler/service/result/builder boundaries
- governance/audit integration

## Runtime chain

`dispatcher -> request schema -> handler -> service -> result object -> response builder -> envelope`

## Responsibility boundaries

- `ExecuteButtonHandlerV2`: use-case entry only; delegates to service and builder.
- `ExecuteButtonServiceV2`: computes minimal execution facts and returns `ExecuteButtonResultV2`.
- `ExecuteButtonResultV2`: boundary object for service output.
- `ExecuteButtonResponseBuilderV2`: transforms result object into stable `data` contract.

## Guard rails

- Dedicated audits:
  - `scripts/verify/v2_execute_button_registry_audit.py`
  - `scripts/verify/v2_execute_button_execution_audit.py`
  - `scripts/verify/v2_execute_button_failure_path_audit.py`
  - `scripts/verify/v2_execute_button_boundary_audit.py`
  - `scripts/verify/v2_execute_button_contract_audit.py`
- Snapshot:
  - `artifacts/v2/execute_button_contract_snapshot_v1.json`

## Frozen output checkpoints

- Envelope root fields: `ok/data/error/meta/effect`
- Meta minimal fields: `intent/trace_id/contract_version/schema_version/latency_ms`
- Data minimal fields:
  `intent/model/method/schema_validated/trace_id/status/version/phase`

## Out of scope

- no real write side-effects in this slice
- no domain business mutation policy in this slice
- no legacy endpoint compatibility bridge in this slice
