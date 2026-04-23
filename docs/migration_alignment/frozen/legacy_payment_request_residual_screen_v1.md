# Legacy Payment Request Residual Screen v1

Status: `PASS`

This is a read-only screen for `C_ZFSQGL` rows not covered by `outflow_request_sc_v1`.

## Result

- raw rows: `13646`
- already assetized rows: `12284`
- residual loadable rows: `0`
- blocked rows: `1362`
- decision: `no_additional_payment_request_assetization_needed`
- DB writes: `0`
- Odoo shell: `false`

## Blocked Reasons

| Reason | Rows |
|---|---:|
| partner_not_assetized | 901 |
| amount_not_positive_or_missing | 224 |
| deleted | 163 |
| project_not_assetized | 115 |
| missing_partner_id | 21 |

## Partner Evidence

| Route | Rows |
|---|---:|
| partner_id_assetized | 12724 |
| partner_id_not_assetized | 901 |
| partner_missing | 21 |

## Decision

`no_additional_payment_request_assetization_needed`

## Boundary

This screen does not generate `payment.request` or change existing outflow assets.
