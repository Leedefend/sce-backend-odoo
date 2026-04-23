# Contract Amount Gap Downstream Screen v1

Status: `PASS`

Target model judgment:

- `construction.contract` does not require a direct amount field.
- Amount totals are computed from optional `construction.contract.line` records.
- Missing old contract amount must not be fabricated into a summary line.

## Result

- amount-gap contracts screened: `51`
- with downstream references: `18`
- without downstream references: `33`
- DB writes: `0`
- Odoo shell: `false`

## Routes

| Route | Rows |
|---|---:|
| keep_header_without_summary_line_downstream_fact_exists | 18 |
| keep_header_without_summary_line_no_downstream_seen | 33 |

## Decision

`amount_gap_contract_headers_kept_without_fabricated_summary_lines`

## Next

Do not generate summary lines for amount-gap contracts; continue with the next business-fact lane.
