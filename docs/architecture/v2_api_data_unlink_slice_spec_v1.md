# v2 API Data Unlink Slice Spec v1

## Scope

This slice defines the ninth reusable v2 mainline pattern around `api.data.unlink`.

Covered layers:

- intent registry reachability
- dispatcher execution closure
- schema validation execution
- handler/service/result/builder boundaries
- governance/audit integration

## Runtime chain

`dispatcher -> request schema -> handler -> service -> result object -> response builder -> envelope`

## Responsibility boundaries

- `ApiDataUnlinkHandlerV2`: use-case entry only; delegates to service and builder.
- `ApiDataUnlinkServiceV2`: computes minimal unlink facts and returns `ApiDataUnlinkResultV2`.
- `ApiDataUnlinkResultV2`: boundary object for service output.
- `ApiDataUnlinkResponseBuilderV2`: transforms result object into stable `data` contract.

## Guard rails

- Dedicated audits:
  - `scripts/verify/v2_api_data_unlink_registry_audit.py`
  - `scripts/verify/v2_api_data_unlink_execution_audit.py`
  - `scripts/verify/v2_api_data_unlink_failure_path_audit.py`
  - `scripts/verify/v2_api_data_unlink_boundary_audit.py`
  - `scripts/verify/v2_api_data_unlink_contract_audit.py`
- Snapshot:
  - `artifacts/v2/api_data_unlink_contract_snapshot_v1.json`

## Frozen output checkpoints

- Envelope root fields: `ok/data/error/meta/effect`
- Meta minimal fields: `intent/trace_id/contract_version/schema_version/latency_ms`
- Data minimal fields:
  `intent/model/ids/schema_validated/trace_id/status/version/phase`

## Out of scope

- no real unlink business execution in this slice
- no unlink policy enforcement in this slice
- no legacy endpoint compatibility bridge in this slice
