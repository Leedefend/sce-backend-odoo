# Legacy Invoice Tax Asset Package v1

Status: `PASS`

This batch turns project-anchored legacy invoice and tax facts into replayable XML assets for `sc.legacy.invoice.tax.fact`.

## Scope

- package id: `legacy_invoice_tax_sc_v1`
- lane: `legacy_invoice_tax`
- layer: `30_relation`
- target model: `sc.legacy.invoice.tax.fact`
- XML: `migration_assets/30_relation/legacy_invoice_tax/legacy_invoice_tax_v1.xml`
- manifest: `migration_assets/manifest/legacy_invoice_tax_asset_manifest_v1.json`
- DB writes: `0`
- Odoo shell: `false`

## Result

- raw source rows: `21323`
- loadable XML records: `5920`
- blocked rows: `15403`
- migration asset bus package count after registration: `20`

## Included Business Facts

| Family | Rows |
|---|---:|
| output_invoice_register | 2881 |
| input_invoice_handover | 1913 |
| prepaid_tax_register | 904 |
| invoice_issue_request | 222 |

## Direction Counts

| Direction | Rows |
|---|---:|
| output_invoice | 3103 |
| input_invoice | 1913 |
| prepaid_tax | 904 |

## Partner Handling

| Partner route | Rows |
|---|---:|
| partner_name_text | 5698 |
| partner_tax_no_text | 222 |

The XML package keeps partner anchoring optional. When old partner ids do not resolve to assetized `res.partner`, the package preserves partner name or tax number as source evidence.

## Blocked Reasons

| Reason | Rows |
|---|---:|
| missing_counterparty_evidence | 14734 |
| amount_and_tax_not_positive_or_missing | 2612 |
| deleted | 623 |
| project_not_assetized | 132 |
| missing_project_id | 9 |

Rows may have more than one blocked reason, so reason counts are diagnostic rather than a unique blocked-row total.

## Boundary

This package preserves invoice and tax historical business facts only.

Excluded from this batch:

- `account.move`
- tax ledger state
- payment state
- settlement state
- runtime approval state
- database integer-id dependencies

## Verification

Commands passed:

```bash
python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-15-MIGRATION-INVOICE-TAX-ASSET-PACKAGE.yaml
python3 -m py_compile scripts/migration/legacy_invoice_tax_asset_generator.py scripts/migration/legacy_invoice_tax_asset_verify.py scripts/migration/migration_asset_bus.py scripts/migration/migration_asset_catalog_verify.py
python3 scripts/migration/legacy_invoice_tax_asset_generator.py --asset-root migration_assets --check
python3 scripts/migration/legacy_invoice_tax_asset_verify.py --asset-root migration_assets --lane legacy_invoice_tax --check
python3 scripts/migration/migration_asset_catalog_verify.py --asset-root migration_assets --catalog migration_assets/manifest/migration_asset_catalog_v1.json --check
python3 scripts/migration/migration_asset_bus.py --verify-only --check
git diff --check
```
