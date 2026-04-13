# v2 API Data Batch Slice Spec v1

## Scope

This slice defines the seventh reusable v2 mainline pattern around `api.data.batch`.

Covered layers:

- intent registry reachability
- dispatcher execution closure
- schema validation execution
- handler/service/result/builder boundaries
- governance/audit integration

## Runtime chain

`dispatcher -> request schema -> handler -> service -> result object -> response builder -> envelope`

## Responsibility boundaries

- `ApiDataBatchHandlerV2`: use-case entry only; delegates to service and builder.
- `ApiDataBatchServiceV2`: computes minimal batch facts and returns `ApiDataBatchResultV2`.
- `ApiDataBatchResultV2`: boundary object for service output.
- `ApiDataBatchResponseBuilderV2`: transforms result object into stable `data` contract.

## Guard rails

- Dedicated audits:
  - `scripts/verify/v2_api_data_batch_registry_audit.py`
  - `scripts/verify/v2_api_data_batch_execution_audit.py`
  - `scripts/verify/v2_api_data_batch_failure_path_audit.py`
  - `scripts/verify/v2_api_data_batch_boundary_audit.py`
  - `scripts/verify/v2_api_data_batch_contract_audit.py`
- Snapshot:
  - `artifacts/v2/api_data_batch_contract_snapshot_v1.json`

## Frozen output checkpoints

- Envelope root fields: `ok/data/error/meta/effect`
- Meta minimal fields: `intent/trace_id/contract_version/schema_version/latency_ms`
- Data minimal fields:
  `intent/model/operation_count/schema_validated/trace_id/status/version/phase`

## Out of scope

- no real batch business execution in this slice
- no batch policy enforcement in this slice
- no legacy endpoint compatibility bridge in this slice
