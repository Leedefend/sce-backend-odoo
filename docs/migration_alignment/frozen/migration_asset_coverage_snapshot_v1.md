# Migration Asset Coverage Snapshot v1

Status: `PASS`

Generated at: `2026-04-15T14:40:00+00:00`

This frozen snapshot records the repository-tracked migration asset bus coverage.
It is no-DB, no-Odoo-shell, and does not materialize any runtime business side
effects.

## Catalog

- catalog: `migration_assets/manifest/migration_asset_catalog_v1.json`
- package count: `17`
- DB writes: `0`
- Odoo shell: `false`

## Package Coverage

| Package | Target model | Layer | Raw rows | Loadable | Blocked/discarded | Risk |
|---|---|---:|---:|---:|---:|---|
| project_sc_v1 | project.project | 10_master | 755 | 755 | 0 | normal |
| partner_sc_v1 | res.partner | 10_master | 10905 | 6541 | 1323 | normal |
| contract_counterparty_partner_sc_v1 | res.partner | 10_master | 88 | 88 | 0 | supplemental_master_data |
| receipt_counterparty_partner_sc_v1 | res.partner | 10_master | 250 | 250 | 0 | supplemental_master_data |
| user_sc_v1 | res.users | 10_master | 101 | 101 | 0 | authority_anchor |
| project_member_sc_v1 | sc.project.member.staging | 30_relation | 21390 | 21390 | 0 | neutral_relation |
| contract_sc_v1 | construction.contract | 20_business | 1694 | 1492 | 202 | anchored_subset |
| contract_line_sc_v1 | construction.contract.line | 20_business | 1694 | 1441 | 51 | summary_fact |
| receipt_sc_v1 | payment.request | 20_business | 7412 | 5355 | 2057 | authorized_receipt_core |
| outflow_request_sc_v1 | payment.request | 20_business | 13646 | 12284 | 1362 | authorized_outflow_request_core |
| actual_outflow_sc_v1 | payment.request | 20_business | 13629 | 12463 | 1166 | draft_actual_outflow_core |
| supplier_contract_sc_v1 | construction.contract | 20_business | 5535 | 5301 | 234 | supplier_contract_header |
| supplier_contract_line_sc_v1 | construction.contract.line | 20_business | 5535 | 5065 | 470 | summary_amount_line |
| outflow_request_line_sc_v1 | payment.request.line | 20_business | 17413 | 15917 | 1496 | line_fact |
| receipt_invoice_line_sc_v1 | sc.receipt.invoice.line | 20_business | 4491 | 4454 | 37 | auxiliary_invoice_line_fact |
| receipt_invoice_attachment_sc_v1 | ir.attachment | 30_relation | 126967 | 1079 | 0 | attachment_url_relation |
| legacy_attachment_backfill_sc_v1 | ir.attachment | 30_relation | 126967 | 18458 | 0 | attachment_url_relation |

## Totals

- raw rows covered: `358472`
- loadable records: `112434`
- blocked/discarded records: `8398`

## Next Lanes

| Priority | Lane | Current blocked | Safe next action |
|---:|---|---:|---|
| 1 | contract_blocker_recovery | 202 | screen remaining deleted/direction/project blockers without weakening project-anchor rule |
| 2 | receipt_blocker_recovery | 2057 | closed_as_invalid_business_data_no_further_recovery |
| 3 | contract_amount_gap | 51 | closed_keep_contract_headers_without_fabricated_summary_lines |
| 4 | outflow_request_assetization | 1362 | closed_core_outflow_request_assets_continue_to_next_business_fact_lane |
| 5 | actual_outflow_assetization | 1166 | closed_draft_actual_outflow_assets_continue_to_supplier_contract_lane |
| 6 | supplier_contract_assetization | 234 | continue_to_supplier_contract_amount_or_line_lane |
| 7 | supplier_contract_line_assetization | 470 | continue_to_receipt_invoice_or_outflow_line_lane |
| 8 | outflow_request_line_assetization | 1496 | closed_line_fact_assets_no_db_replay_in_this_stage |
| 9 | receipt_invoice_line_assetization | 37 | continue_to_receipt_invoice_line_usability_or_attachment_index_lane |
| 10 | receipt_invoice_attachment_assetization | 0 | continue_to_next_legacy_business_fact_lane_or_binary_file_custody_plan |
| 11 | legacy_attachment_backfill_assetization | 0 | continue_to_binary_file_custody_plan_or_next_business_fact_lane |

## Decision

`coverage_snapshot_frozen_no_db_replay_continue_business_fact_assetization`
