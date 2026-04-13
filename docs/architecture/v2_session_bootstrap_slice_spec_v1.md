# v2 Session Bootstrap Slice Spec v1

## Scope

This slice defines the first reusable v2 mainline pattern around `session.bootstrap`.

Covered layers:

- intent registry reachability
- dispatcher execution closure
- schema validation execution
- handler/service/result/builder boundaries
- governance/audit integration

## Runtime chain

`dispatcher -> request schema -> handler -> service -> result object -> response builder -> envelope`

## Responsibility boundaries

- `SessionBootstrapHandlerV2`: use-case entry, delegates to service and builder only.
- `SessionBootstrapServiceV2`: computes business-neutral bootstrap facts and returns `SessionBootstrapResultV2`.
- `SessionBootstrapResultV2`: immutable boundary object for service output.
- `SessionBootstrapResponseBuilderV2`: transforms result object into stable `data` contract.

## Guard rails

- Dedicated audits:
  - `scripts/verify/v2_session_bootstrap_execution_audit.py`
  - `scripts/verify/v2_session_bootstrap_failure_path_audit.py`
  - `scripts/verify/v2_session_bootstrap_boundary_audit.py`
  - `scripts/verify/v2_session_bootstrap_contract_audit.py`
- Snapshot:
  - `artifacts/v2/session_bootstrap_contract_snapshot_v1.json`

## Frozen output checkpoints

- Envelope root fields: `ok/data/error/meta/effect`
- Meta minimal fields: `intent/trace_id/contract_version/schema_version/latency_ms`
- Data minimal fields:
  `intent/session_status/bootstrap_ready/schema_validated/app_key/user_id/company_id/trace_id/registry_count/phase/version`

## Out of scope

- no `ui.contract` migration
- no `meta.describe_model` migration in this slice
- no legacy endpoint compatibility bridge in this slice
