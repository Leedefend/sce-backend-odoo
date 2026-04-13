# v2 API Data Slice Spec v1

## Scope

This slice defines the fifth reusable v2 mainline pattern around `api.data`.

Covered layers:

- intent registry reachability
- dispatcher execution closure
- schema validation execution
- handler/service/result/builder boundaries
- governance/audit integration

## Runtime chain

`dispatcher -> request schema -> handler -> service -> result object -> response builder -> envelope`

## Responsibility boundaries

- `ApiDataHandlerV2`: use-case entry only; delegates to service and builder.
- `ApiDataServiceV2`: computes minimal operation facts and returns `ApiDataResultV2`.
- `ApiDataResultV2`: boundary object for service output.
- `ApiDataResponseBuilderV2`: transforms result object into stable `data` contract.

## Guard rails

- Dedicated audits:
  - `scripts/verify/v2_api_data_registry_audit.py`
  - `scripts/verify/v2_api_data_execution_audit.py`
  - `scripts/verify/v2_api_data_failure_path_audit.py`
  - `scripts/verify/v2_api_data_boundary_audit.py`
  - `scripts/verify/v2_api_data_contract_audit.py`
- Snapshot:
  - `artifacts/v2/api_data_contract_snapshot_v1.json`

## Frozen output checkpoints

- Envelope root fields: `ok/data/error/meta/effect`
- Meta minimal fields: `intent/trace_id/contract_version/schema_version/latency_ms`
- Data minimal fields:
  `intent/model/operation/schema_validated/trace_id/status/version/phase`

## Out of scope

- no real data read/write behavior in this slice
- no domain business policy enforcement in this slice
- no legacy endpoint compatibility bridge in this slice
