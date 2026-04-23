# Legacy Actual Outflow Fact Screen v1

Status: `PASS`

Source: `legacy-sqlserver:LegacyDb.dbo.T_FK_Supplier`

This is a direct legacy database, read-only screen for actual outflow facts.
It checks project_anchor, partner_anchor, positive amount, stable row id, and
optional outflow request_anchor against repository migration assets.

## Result

- raw rows: `13629`
- loadable candidates: `12463`
- blocked/discarded rows: `1166`
- DB writes: `0`
- Odoo shell: `false`

## Routes

| Route | Rows |
|---|---:|
| block_partner_anchor_missing | 776 |
| block_project_anchor_missing | 111 |
| discard_deleted_source | 56 |
| discard_non_positive_amount | 223 |
| loadable_candidate_request_optional | 12463 |

## Blockers

| Blocker | Rows |
|---|---:|
| discard_deleted | 56 |
| missing_partner_ref | 4 |
| partner_not_in_asset | 814 |
| project_not_in_asset | 111 |
| zero_or_negative_amount | 227 |

## Request Anchor

| request_anchor | Rows |
|---|---:|
| request_empty | 62 |
| request_resolved | 12283 |
| request_unresolved | 118 |

## Supplier Contract Presence

| supplier_contract | Rows |
|---|---:|
| supplier_contract_empty | 12463 |

## Decision

`actual_outflow_screen_pass_asset_generation_next_after_owner_accepts_contract_optional_policy`

## Next

Generate actual outflow assets with optional outflow_request_id and deferred supplier_contract_id, or first assetize supplier contracts if contract anchoring must be mandatory.
