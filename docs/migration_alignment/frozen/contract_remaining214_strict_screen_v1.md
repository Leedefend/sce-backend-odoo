# Contract Remaining 214 Strict Screen v1

Status: `PASS`

This screen keeps the strict contract fact policy:

- deleted source rows are not migrated
- income/expense direction must have explicit old-database evidence
- project body anchor must exist before a contract fact can load

## Result

- screened blocked rows: `202`
- recoverable candidates without weakening conditions: `0`
- DB writes: `0`
- Odoo shell: `false`

## Strict Routes

| Route | Rows |
|---|---:|
| block_direction_not_explicit | 49 |
| block_project_anchor_missing | 88 |
| discard_deleted_source | 65 |

## Blockers

| Blocker | Rows |
|---|---:|
| deleted_flag | 65 |
| direction_defer | 124 |
| partner_anchor_ambiguous | 2 |
| partner_anchor_missing | 128 |
| project_anchor_missing | 88 |

## Evidence

- receipt-direction candidates: `0`
- alternate project-reference hits: `11`

## Decision

`strict_screen_pass_no_recoverable_contract_candidates`

## Next

Keep remaining contract rows blocked under the strict policy; move to receipt blocker classification or contract amount-gap screening.
