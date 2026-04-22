# Legacy Receipt Income Residual Screen v1

Status: `PASS`

This is a read-only screen for receipt and income facts not already covered by `receipt_sc_v1`.

## Result

- raw rows: `14769`
- already assetized rows: `5355`
- residual loadable rows: `7220`
- blocked rows: `2194`
- DB writes: `0`
- Odoo shell: `false`

## Source table readiness

| Source table | Raw rows | Residual loadable candidates |
|---|---:|---:|
| C_JFHKLR | 7412 | 10 |
| C_CWSFK_GSCWSR | 4702 | 4674 |
| ZJGL_SZQR_DKQRB | 2655 | 2536 |

## Blocked Reasons

| Reason | Rows |
|---|---:|
| amount_not_positive_or_missing | 1976 |
| missing_project_id | 1884 |
| project_not_assetized | 118 |
| deleted | 110 |

## Family Counts

| Family | Rows |
|---|---:|
| customer_receipt | 7412 |
| company_financial_income | 4702 |
| receipt_confirmation | 2655 |

## Partner Evidence

| Route | Rows |
|---|---:|
| partner_id_assetized | 10568 |
| partner_name_text | 2581 |
| partner_id_not_assetized | 1530 |
| partner_missing | 90 |

## Next lane recommendation

- lane: `legacy_receipt_income_residual_fact_carrier`
- source table priority: `C_CWSFK_GSCWSR`
- residual loadable rows: `4674`
- reason: screen found project-anchored positive-amount income facts not already covered by receipt_sc_v1

## Boundary

These rows are receipt or income business facts, not payment runtime, settlement, or accounting entries.
A later carrier must not create `payment.request`, `account.move`, settlement state, or approval runtime facts.
