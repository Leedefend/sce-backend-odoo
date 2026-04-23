# Legacy Supplier Contract Fact Screen v1

Status: `PASS`

This is a read-only old-database screen for `supplier_contract` facts before
asset generation. It performs no DB write and does not generate XML assets.

## Required Facts

- stable supplier contract source id
- contract identity
- project_anchor
- partner_anchor

Amount is `amount_optional`: it may be preserved when positive, but it must not
block contract header assetization and must not be fabricated.

## Result

- source table: `T_GYSHT_INFO`
- raw rows: `5535`
- loadable candidates: `5301`
- blocked/discarded rows: `234`
- target model candidate: `construction.contract`
- DB writes: `0`
- Odoo shell: `false`

## Routes

| Route | Rows |
|---|---:|
| block_partner_anchor_missing | 119 |
| block_project_anchor_missing | 22 |
| discard_deleted_source | 93 |
| loadable_candidate_amount_optional | 5301 |

## Blockers

| Blocker | Rows |
|---|---:|
| discard_deleted | 93 |
| partner_not_in_asset | 132 |
| project_not_in_asset | 22 |

## Amount Policy

| Policy | Rows |
|---|---:|
| amount_optional_blank_or_zero | 243 |
| amount_positive | 5292 |

## Decision

`supplier_contract facts can proceed to carrier mapping. amount_optional is required because the target contract header does not require amount and summary amount must not be fabricated.`

## Next

screen target construction.contract carrier fields for supplier_contract XML asset generation
