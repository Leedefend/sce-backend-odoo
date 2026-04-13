# v2 Load Contract Slice Spec v1

## Scope

This slice defines the twelfth reusable v2 mainline pattern around `load_contract`.

Covered layers:

- intent registry reachability
- dispatcher execution closure
- schema validation execution
- handler/service/result/builder boundaries
- governance/audit integration

## Runtime chain

`dispatcher -> request schema -> handler -> service -> result object -> response builder -> envelope`

## Responsibility boundaries

- `LoadContractHandlerV2`: use-case entry only; delegates to service and builder.
- `LoadContractServiceV2`: computes minimal contract-loading facts and returns `LoadContractResultV2`.
- `LoadContractResultV2`: boundary object for service output.
- `LoadContractResponseBuilderV2`: transforms result object into stable `data` contract.

## Guard rails

- Dedicated audits:
  - `scripts/verify/v2_load_contract_registry_audit.py`
  - `scripts/verify/v2_load_contract_execution_audit.py`
  - `scripts/verify/v2_load_contract_failure_path_audit.py`
  - `scripts/verify/v2_load_contract_boundary_audit.py`
  - `scripts/verify/v2_load_contract_contract_audit.py`
- Snapshot:
  - `artifacts/v2/load_contract_contract_snapshot_v1.json`

## Frozen output checkpoints

- Envelope root fields: `ok/data/error/meta/effect`
- Meta minimal fields: `intent/trace_id/contract_version/schema_version/latency_ms`
- Data minimal fields:
  `intent/model/view_type/schema_validated/trace_id/status/version/phase`

## Out of scope

- no real load_contract business execution in this slice
- no view-parser deep orchestration in this slice
- no legacy endpoint compatibility bridge in this slice
