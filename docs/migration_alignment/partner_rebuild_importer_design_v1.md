# Partner Rebuild Importer Design v1

Iteration: `ITER-2026-04-13-1851`

## Objective

Promote the partner strong-evidence dry-run into a repeatable full-rebuild importer shape without enabling database writes.

This importer is a rebuild-pipeline component, not a one-off import script. It validates input shape, produces deterministic row decisions, records a run id, and emits machine-readable outputs for the next gated batch.

## Scope

Allowed in this version:

- Read `artifacts/migration/partner_strong_evidence_dry_run_input_v1.csv`.
- Validate required input columns.
- Compare candidate partner names with the current `res.partner` baseline exported to `artifacts/migration/contract_partner_baseline_v1.json`.
- Emit row-level audit decisions to `artifacts/migration/partner_rebuild_importer_rows_v1.csv`.
- Emit summary metrics to `artifacts/migration/partner_rebuild_importer_result_v1.json`.

Explicitly not allowed in this version:

- No database write.
- No ORM call.
- No partner creation.
- No contract import.
- No project import.
- No partner merge.

## Input Contract

Required columns:

- `legacy_partner_id`
- `partner_name`
- `company_credit_code`
- `company_tax_no`
- `source`
- `source_evidence`
- `linked_contract_count`
- `linked_repayment_rows`

The current accepted source is `T_Base_CooperatCompany` because the database evidence shows it is the primary partner source. `T_Base_SupplierInfo` remains supplemental and is not accepted as a primary partner-create source in this importer version.

## Matching Strategy

The importer uses a conservative no-write decision model:

- `reuse_existing_exact`: exactly one existing partner matches the input name.
- `reuse_existing_normalized`: exactly one existing partner matches after punctuation/space/common suffix normalization.
- `manual_review_existing_duplicate`: multiple existing matches are found.
- `create_candidate`: no existing match is found and the row passes mandatory input checks.
- `reject`: mandatory identity/source/name checks fail.

The importer does not decide final creation authority. `create_candidate` only means the row is safe enough to enter a later write-mode gate.

## Output Contract

Row-level audit CSV columns:

- `run_id`
- `row_no`
- `legacy_partner_id`
- `partner_name`
- `source`
- `dry_run_action`
- `blockers`
- `matched_partner_ids`
- `linked_contract_count`
- `linked_repayment_rows`

Summary JSON fields:

- `status`
- `mode`
- `run_id`
- `input`
- `input_rows`
- `output_rows`
- `action_counts`
- `blocker_counts`
- `output_csv`
- `decision`
- `next_step`

## Rebuild Policy

`legacy_partner_id` remains the primary rebuild identity for this strong-evidence slice. Credit code and tax number coverage are too sparse in the 369-row slice to be the primary lock key.

Write mode remains blocked until a dedicated partner write-mode gate defines sample size, idempotency behavior, rollback criteria, and Odoo-side validation.
