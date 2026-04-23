# Legacy Supplier Contract Line Screen v1

Status: `PASS`

This is a read-only old-database screen for supplier contract amount facts
before construction.contract.line asset generation.

## Required Facts

- supplier_contract_anchor
- amount_positive

The target is `construction.contract.line`. The header amount is
`header_amount_not_written`; construction.contract header totals must be
computed from line facts.

## Result

- source table: `T_GYSHT_INFO`
- raw rows: `5535`
- loadable candidates: `5065`
- blocked/discarded rows: `470`
- target model candidate: `construction.contract.line`
- DB writes: `0`
- Odoo shell: `false`

## Routes

| Route | Rows |
|---|---:|
| block_amount_not_positive | 236 |
| block_supplier_contract_anchor_missing | 141 |
| discard_deleted_source | 93 |
| loadable_candidate_amount_line | 5065 |

## Blockers

| Blocker | Rows |
|---|---:|
| amount_not_positive | 243 |
| discard_deleted | 93 |
| supplier_contract_anchor_missing | 234 |

## Amount Sources

| Source | Rows |
|---|---:|
| ZJE | 5065 |

## Decision

`supplier_contract line amount facts can proceed to carrier mapping and XML generation`

## Next

freeze construction.contract.line carrier boundary and generate supplier_contract_line XML assets
