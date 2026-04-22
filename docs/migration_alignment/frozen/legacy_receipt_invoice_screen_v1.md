# Legacy Receipt Invoice Screen v1

Status: `PASS`

This is a read-only screen for legacy receipt invoice line facts before XML
asset generation.

## Result

- source table: `C_JFHKLR_CB`
- raw rows: `4491`
- loadable candidates: `4454`
- blocked rows: `37`
- carrier decision: `no_safe_existing_xml_carrier`
- DB writes: `0`
- Odoo shell: `false`

## Routes

| Route | Rows |
|---|---:|
| block_amount_not_positive | 9 |
| block_receipt_anchor_missing | 28 |
| loadable_candidate_invoice_fact | 4454 |

## Blockers

| Blocker | Rows |
|---|---:|
| amount_not_positive | 10 |
| receipt_anchor_missing | 28 |

## Amount Sources

| Source | Rows |
|---|---:|
| KPJE | 4454 |

## Rejected Carriers

- `account.move`: accounting truth and posting semantics; forbidden for auxiliary receipt invoice facts
- `sc.settlement.order.invoice_*`: header placeholder fields; cannot preserve multiple invoice lines per receipt
- `payment.request.note`: unstructured text cannot provide replayable line facts

## Decision

`new_receipt_invoice_line_carrier_required`
