# v2 API Onchange Slice Spec v1

## Scope

This slice defines the sixth reusable v2 mainline pattern around `api.onchange`.

Covered layers:

- intent registry reachability
- dispatcher execution closure
- schema validation execution
- handler/service/result/builder boundaries
- governance/audit integration

## Runtime chain

`dispatcher -> request schema -> handler -> service -> result object -> response builder -> envelope`

## Responsibility boundaries

- `ApiOnchangeHandlerV2`: use-case entry only; delegates to service and builder.
- `ApiOnchangeServiceV2`: computes minimal onchange facts and returns `ApiOnchangeResultV2`.
- `ApiOnchangeResultV2`: boundary object for service output.
- `ApiOnchangeResponseBuilderV2`: transforms result object into stable `data` contract.

## Guard rails

- Dedicated audits:
  - `scripts/verify/v2_api_onchange_registry_audit.py`
  - `scripts/verify/v2_api_onchange_execution_audit.py`
  - `scripts/verify/v2_api_onchange_failure_path_audit.py`
  - `scripts/verify/v2_api_onchange_boundary_audit.py`
  - `scripts/verify/v2_api_onchange_contract_audit.py`
- Snapshot:
  - `artifacts/v2/api_onchange_contract_snapshot_v1.json`

## Frozen output checkpoints

- Envelope root fields: `ok/data/error/meta/effect`
- Meta minimal fields: `intent/trace_id/contract_version/schema_version/latency_ms`
- Data minimal fields:
  `intent/model/field_name/schema_validated/trace_id/status/version/phase`

## Out of scope

- no real onchange business linkage in this slice
- no field-rule policy enforcement in this slice
- no legacy endpoint compatibility bridge in this slice
