# SCBS Mapping Decision Readiness

Database: `sc_prod_sim`

## Current Fact Gate

| staged_rows | staged_amount | blocked_rows | staging_ready | conflict | projection_ready |
| --- | --- | --- | --- | --- | --- |
| 15190 | 2,012,171,862.45 | 0 | 0 | 0 | 15190 |

## Remaining Gap

- Missing-map technical blockage: `0` rows.
- Conflict review queue: `551` rows, amount `51,298,836.24`.
- Mapping review workbook rows: `0`.
- Validation baseline: `{}`.
- Batch status baseline: `{}`.

## Action Summary

| dimension | suggested_action | mapping_rows | fact_rows | fact_amount | with_target |
| --- | --- | --- | --- | --- | --- |

## Batch Status

| suggested_action | batch_status | row_count | decided_rows | blank_rows | error_rows | fact_rows | fact_amount |
| --- | --- | --- | --- | --- | --- | --- | --- |

## Projection Simulation

| simulated_gate | rows | amount_total |
| --- | --- | --- |
| projection_ready | 15190 | 2,012,171,862.45 |

## Execution Order

1. Fill `01_manual_partner_required` using partner target candidates.
2. Fill `02_review_non_counterparty_label` with business treatment: confirm, ignore, or keep conflict.
3. Fill `03_choose_target_partner` using partner target candidates.
4. Fill test/non-real batches as ignore or conflict.
5. Fill business entity and project batches using consolidation and target candidate reports.
6. Fill normal partner batch.
7. Run batch validation until target batches are `READY` or intentionally `PARTIAL`.
8. Run per-batch validate, dry-run apply, write apply, then rerun staging reconciliation.

## Current Conclusion

The technical staging and missing-map gates are closed. The upgrade is waiting on business mapping decisions before any formal projection can be opened.
