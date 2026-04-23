# Contract Header 12-Row Dry-Run v1

## Scope

- Task: `ITER-2026-04-13-1863`
- Mode: no-DB dry-run
- Input: `artifacts/migration/contract_anchor_safe_candidates_v1.csv`
- Output:
  - `artifacts/migration/contract_header_12_row_dry_run_rows_v1.csv`
  - `artifacts/migration/contract_header_12_row_dry_run_result_v1.json`

## Result

- Dry-run rows: 12
- Ready for readonly DB precheck: 12
- Blocked rows: 0
- Contract type distribution: `out=12`
- Legacy status distribution: `2=12`
- Contract write authorization: not granted
- Contract write decision: NO-GO until explicit contract write authorization plus DB precheck

## Payload Policy

The dry-run payload keeps the first contract materialization slice to header
identity and anchor fields only:

- `legacy_contract_id`
- `legacy_project_id`
- `project_id`
- `partner_id`
- `subject`
- `type`
- `legacy_contract_no`
- `legacy_document_no`
- `legacy_external_contract_no`
- `legacy_status`
- `legacy_deleted_flag`
- `legacy_counterparty_text`

`tax_id` and `name` are intentionally not prefilled in the local dry-run. The
current model can derive these through default tax policy and sequence behavior,
but that must be validated by a readonly DB precheck before any write batch.

## Remaining Gate

Before any contract write batch, run a dedicated readonly DB precheck for:

- default tax availability for `out` contracts
- contract sequence availability
- `legacy_contract_id` uniqueness in the target DB
- continued existence of the mapped `project_id` and `partner_id`

This batch did not create or update `construction.contract`.
