# Receipt Blocker Strict Screen v1

Status: `PASS`

This screen keeps the strict receipt fact policy:

- deleted source rows are discarded
- zero or negative amount rows are discarded
- project-missing rows are discarded by owner decision
- incomplete-counterparty rows are discarded by owner decision

## Result

- source rows: `7412`
- current loadable rows: `5355`
- blocked rows screened: `2057`
- recoverable candidate rows: `0`
- discard rows: `2057`
- DB writes: `0`
- Odoo shell: `false`

## Strict Routes

| Route | Rows |
|---|---:|
| discard_deleted_source | 49 |
| discard_incomplete_counterparty | 10 |
| discard_non_positive_amount | 1908 |
| discard_project_anchor_missing | 90 |

## Blockers

| Blocker | Rows |
|---|---:|
| discard_deleted | 49 |
| missing_partner_ref | 16 |
| partner_not_in_asset | 329 |
| project_not_in_asset | 1975 |
| zero_or_negative_amount | 1908 |

## Decision

`remaining_receipt_blockers_discarded_as_invalid_business_data`

## Next

Receipt blocker recovery lane is closed; continue with contract amount-gap screening or the next business-fact lane.
