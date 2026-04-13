# v2 File Download Slice Spec v1

## Scope

This slice defines the eleventh reusable v2 mainline pattern around `file.download`.

Covered layers:

- intent registry reachability
- dispatcher execution closure
- schema validation execution
- handler/service/result/builder boundaries
- governance/audit integration

## Runtime chain

`dispatcher -> request schema -> handler -> service -> result object -> response builder -> envelope`

## Responsibility boundaries

- `FileDownloadHandlerV2`: use-case entry only; delegates to service and builder.
- `FileDownloadServiceV2`: computes minimal download facts and returns `FileDownloadResultV2`.
- `FileDownloadResultV2`: boundary object for service output.
- `FileDownloadResponseBuilderV2`: transforms result object into stable `data` contract.

## Guard rails

- Dedicated audits:
  - `scripts/verify/v2_file_download_registry_audit.py`
  - `scripts/verify/v2_file_download_execution_audit.py`
  - `scripts/verify/v2_file_download_failure_path_audit.py`
  - `scripts/verify/v2_file_download_boundary_audit.py`
  - `scripts/verify/v2_file_download_contract_audit.py`
- Snapshot:
  - `artifacts/v2/file_download_contract_snapshot_v1.json`

## Frozen output checkpoints

- Envelope root fields: `ok/data/error/meta/effect`
- Meta minimal fields: `intent/trace_id/contract_version/schema_version/latency_ms`
- Data minimal fields:
  `intent/model/res_id/name/schema_validated/trace_id/status/version/phase`

## Out of scope

- no real download business execution in this slice
- no download policy enforcement in this slice
- no legacy endpoint compatibility bridge in this slice
