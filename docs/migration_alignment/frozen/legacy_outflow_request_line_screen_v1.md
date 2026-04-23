# Legacy Outflow Request Line Screen v1

Status: `PASS`

This is a read-only old-database screen for outflow request `line_fact` rows
before target carrier selection.

## Required Facts

- stable line id
- outflow_request_anchor
- amount_positive

Supplier contract anchor is optional at this stage because many source rows
only carry parent request and amount facts.

## Result

- source table: `C_ZFSQGL_CB`
- raw rows: `17413`
- loadable candidates: `15917`
- blocked/discarded rows: `1496`
- target model candidate: `carrier_not_selected`
- DB writes: `0`
- Odoo shell: `false`

## Routes

| Route | Rows |
|---|---:|
| block_amount_not_positive | 608 |
| block_outflow_request_anchor_missing | 888 |
| loadable_candidate_line_fact | 15917 |

## Blockers

| Blocker | Rows |
|---|---:|
| amount_not_positive | 816 |
| outflow_request_anchor_missing | 888 |

## Amount Sources

| Source | Rows |
|---|---:|
| CCZFJE | 70 |
| ZJE | 15847 |

## Supplier Contract Anchor

| Status | Rows |
|---|---:|
| supplier_contract_anchor_empty | 850 |
| supplier_contract_anchor_resolved | 6779 |
| supplier_contract_anchor_unresolved | 9784 |

## Decision

`outflow_request line_fact candidates require a carrier screen before XML generation`

## Next

screen target carrier for outflow_request_line facts; do not weaken parent anchor requirement
