# Legacy Invoice Tax Fact Screen v1

Status: `PASS`

This is a read-only screen for invoice and tax-related legacy facts.

## Result

- raw rows: `29987`
- loadable rows: `26700`
- blocked rows: `3287`
- DB writes: `0`
- Odoo shell: `false`

## Source table readiness

| Source table | Raw rows | Loadable candidates |
|---|---:|---:|
| C_JXXP_ZYFPJJD_CB | 25280 | 22660 |
| C_JXXP_XXKPDJ | 3157 | 2907 |
| C_JXXP_YJSKDJ | 1290 | 908 |
| C_JXXP_KJFPSQ | 260 | 225 |

## Blocked Reasons

| Reason | Rows |
|---|---:|
| amount_and_tax_missing_or_zero | 2427 |
| deleted | 683 |
| project_not_assetized | 186 |
| missing_counterparty_evidence | 96 |
| missing_project_id | 7 |

## Family Counts

| Family | Rows |
|---|---:|
| input_invoice_handover | 25280 |
| output_invoice_register | 3157 |
| prepaid_tax_register | 1290 |
| invoice_issue_request | 260 |

## Partner Evidence

| Route | Rows |
|---|---:|
| partner_id_assetized | 21213 |
| partner_id_not_assetized | 4720 |
| partner_name_text | 3697 |
| partner_tax_no_text | 264 |
| partner_missing | 93 |

## Next lane recommendation

- lane: `legacy_invoice_tax_fact_carrier`
- source table priority: `C_JXXP_ZYFPJJD_CB`
- loadable rows: `22660`
- reason: screen found project-anchored invoice/tax facts; design a neutral carrier before XML generation

## Boundary

These rows are invoice and tax business facts, not accounting entries.
A later carrier must not create `account.move`, payment, settlement, tax ledger, or approval runtime facts.
