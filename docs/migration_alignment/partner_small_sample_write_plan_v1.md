# Partner Small-Sample Write Plan v1

Iteration: `ITER-2026-04-13-1852`

## Purpose

Define the smallest useful partner write test for the repeatable full-rebuild migration pipeline.

This document does not authorize execution. It defines the execution shape for a later dedicated write batch.

## Recommended Sample

Recommended sample size: 30 rows.

Source:

- `artifacts/migration/partner_rebuild_importer_rows_v1.csv`

Selection rule:

1. Only rows with `dry_run_action = create_candidate`.
2. Only rows with non-empty `legacy_partner_id`.
3. Only rows with `source = T_Base_CooperatCompany`.
4. Prefer rows with higher `linked_contract_count` and `linked_repayment_rows` because those rows have stronger downstream business value.
5. Keep the sample bounded at 30 rows.

## Write Mode

First write batch mode: `create-only`.

Allowed behavior:

- Search by `legacy_partner_source + legacy_partner_id`.
- If no existing partner is found, create one partner using the safe field set.
- If an existing partner is found, skip and report `existing_legacy_identity`.

Forbidden behavior:

- No update of existing partner.
- No merge.
- No contract backfill.
- No supplier supplement write.
- No bank data write.
- No payment/receipt/settlement logic.

## Expected Output Artifacts For The Future Write Batch

The future write batch should emit:

- selected sample CSV,
- write result JSON,
- write row audit CSV,
- post-write readonly review report,
- rollback target list,
- rollback dry-run result.

## Acceptance Criteria For The Future Write Batch

The future write batch can pass only if:

1. selected rows are exactly from the 369-row no-DB importer output;
2. all written rows are create-only or skip-only;
3. no update occurs;
4. every created row has `legacy_partner_source = cooperat_company`;
5. every created row has non-empty `legacy_partner_id`;
6. every created row has `legacy_source_evidence`;
7. post-write readonly review confirms the exact created count;
8. rollback target list locks only by `legacy_partner_source + legacy_partner_id`;
9. rollback dry-run identifies only the created sample rows.

## Decision

Do not write partners in `ITER-2026-04-13-1852`.

The next write-capable batch should be named as a dedicated partner small-sample create-only batch and should require explicit authorization before execution.
