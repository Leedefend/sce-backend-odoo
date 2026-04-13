# v2 Meta Describe Model Slice Spec v1

## Scope

This slice defines the second reusable v2 mainline pattern around `meta.describe_model`.

Covered layers:

- intent registry reachability
- dispatcher execution closure
- schema validation execution
- handler/service/result/builder boundaries
- governance/audit integration

## Runtime chain

`dispatcher -> request schema -> handler -> service -> result object -> response builder -> envelope`

## Responsibility boundaries

- `MetaDescribeModelHandlerV2`: use-case entry only; delegates to service and builder.
- `MetaDescribeModelServiceV2`: computes describe-model facts and returns `MetaDescribeModelResultV2`.
- `MetaDescribeModelResultV2`: immutable boundary object for service output.
- `MetaDescribeModelResponseBuilderV2`: transforms result object into stable `data` contract.

## Guard rails

- Dedicated audits:
  - `scripts/verify/v2_meta_describe_model_registry_audit.py`
  - `scripts/verify/v2_meta_describe_model_execution_audit.py`
  - `scripts/verify/v2_meta_describe_model_failure_path_audit.py`
  - `scripts/verify/v2_meta_describe_model_boundary_audit.py`
  - `scripts/verify/v2_meta_describe_model_contract_audit.py`
- Snapshot:
  - `artifacts/v2/meta_describe_model_contract_snapshot_v1.json`

## Frozen output checkpoints

- Envelope root fields: `ok/data/error/meta/effect`
- Meta minimal fields: `intent/trace_id/contract_version/schema_version/latency_ms`
- Data minimal fields:
  `intent/model/display_name/fields/capabilities/source/version/schema_validated/phase`

## Out of scope

- no `ui.contract` migration in this slice
- no full field/modifier parser baseline in this slice
- no legacy endpoint compatibility bridge in this slice
