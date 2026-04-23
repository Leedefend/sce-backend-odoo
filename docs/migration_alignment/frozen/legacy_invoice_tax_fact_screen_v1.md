# Legacy Invoice Tax Fact Screen v1

Status: `PASS`

This is a read-only screen for invoice and tax-related legacy facts.

## Result

- raw rows: `21323`
- loadable rows: `5920`
- blocked rows: `15403`
- DB writes: `0`
- Odoo shell: `false`

## Source table readiness

| Source table | Raw rows | Loadable candidates |
|---|---:|---:|
| C_JXXP_ZYFPJJD | 16616 | 1913 |
| C_JXXP_XXKPDJ | 3157 | 2881 |
| C_JXXP_YJSKDJ | 1290 | 904 |
| C_JXXP_KJFPSQ | 260 | 222 |

## Blocked Reasons

| Reason | Rows |
|---|---:|
| missing_counterparty_evidence | 14734 |
| amount_and_tax_not_positive_or_missing | 2612 |
| deleted | 623 |
| project_not_assetized | 132 |
| missing_project_id | 9 |

## Family Counts

| Family | Rows |
|---|---:|
| input_invoice_handover | 16616 |
| output_invoice_register | 3157 |
| prepaid_tax_register | 1290 |
| invoice_issue_request | 260 |

## Partner Evidence

| Route | Rows |
|---|---:|
| partner_missing | 14731 |
| partner_name_text | 5670 |
| partner_id_not_assetized | 662 |
| partner_tax_no_text | 260 |

## Next lane recommendation

- lane: `legacy_invoice_tax_fact_carrier`
- source table priority: `C_JXXP_XXKPDJ`
- loadable rows: `2881`
- reason: screen found project-anchored invoice/tax facts; design a neutral carrier before XML generation

## Boundary

These rows are invoice and tax business facts, not accounting entries.
A later carrier must not create `account.move`, payment, settlement, tax ledger, or approval runtime facts.
