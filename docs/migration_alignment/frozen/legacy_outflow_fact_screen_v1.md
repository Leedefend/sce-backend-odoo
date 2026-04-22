# Legacy Outflow Fact Screen v1

Status: `PASS`

This is a no-DB screen for old-system outflow request facts before any target
asset generation. The target carrier is `payment.request(type='pay')`, so this
lane remains high-risk until separately authorized for asset generation.

## Required Facts

- stable old row id
- project anchor
- partner anchor
- positive amount

Contract reference is optional.

## Result

- raw rows: `13646`
- loadable candidates: `12284`
- blocked/discarded rows: `1362`
- contract-linked candidate rows: `0`
- DB writes: `0`
- Odoo shell: `false`

## Routes

| Route | Rows |
|---|---:|
| block_partner_anchor_missing | 861 |
| block_project_anchor_missing | 115 |
| discard_deleted_source | 163 |
| discard_non_positive_amount | 223 |
| loadable_candidate_contract_optional | 12284 |

## Blockers

| Blocker | Rows |
|---|---:|
| discard_deleted | 163 |
| missing_partner_ref | 21 |
| partner_not_in_asset | 901 |
| project_not_in_asset | 115 |
| zero_or_negative_amount | 224 |

## Amount Sources

| Source | Rows |
|---|---:|
| f_JHJE | 12284 |

## Decision

`outflow_fact_screen_pass_asset_generation_requires_dedicated_authorization`

## Next

Open a dedicated outflow asset generation task only after confirming high-risk financial lane authorization.
