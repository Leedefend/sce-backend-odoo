# Legacy Receipt Income Asset Package v1

Status: `PASS`

This batch turns residual project-anchored legacy receipt and income facts into replayable XML assets for `sc.legacy.receipt.income.fact`.

## Scope

- package id: `legacy_receipt_income_sc_v1`
- lane: `legacy_receipt_income`
- layer: `30_relation`
- target model: `sc.legacy.receipt.income.fact`
- XML: `migration_assets/30_relation/legacy_receipt_income/legacy_receipt_income_v1.xml`
- manifest: `migration_assets/manifest/legacy_receipt_income_asset_manifest_v1.json`
- DB writes: `0`
- Odoo shell: `false`

## Result

- raw source rows: `14769`
- already covered by `receipt_sc_v1`: `5355`
- loadable XML records: `7220`
- blocked rows: `2194`
- migration asset bus package count after registration: `21`

## Included Business Facts

| Family | Rows |
|---|---:|
| company_financial_income | 4674 |
| receipt_confirmation | 2536 |
| customer_receipt | 10 |

## Partner Handling

| Partner route | Rows |
|---|---:|
| partner_ref | 3476 |
| partner_name_text | 2481 |
| partner_text_id | 1198 |
| partner_missing | 65 |

Partner anchoring is optional for this historical carrier. Project anchor and positive amount are mandatory.

## Blocked Reasons

| Reason | Rows |
|---|---:|
| amount_not_positive_or_missing | 1976 |
| missing_project_id | 1884 |
| project_not_assetized | 118 |
| deleted | 110 |

Rows may have more than one blocked reason, so reason counts are diagnostic rather than a unique blocked-row total.

## Boundary

This package preserves residual receipt/income historical business facts only.

Excluded from this batch:

- `payment.request`
- `account.move`
- settlement state
- runtime approval state
- database integer-id dependencies

## Verification

Commands passed:

```bash
python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-15-MIGRATION-RECEIPT-INCOME-ASSET-PACKAGE.yaml
python3 -m py_compile scripts/migration/legacy_receipt_income_asset_generator.py scripts/migration/legacy_receipt_income_asset_verify.py scripts/migration/migration_asset_bus.py scripts/migration/migration_asset_catalog_verify.py
python3 scripts/migration/legacy_receipt_income_asset_generator.py --asset-root migration_assets --check
python3 scripts/migration/legacy_receipt_income_asset_verify.py --asset-root migration_assets --lane legacy_receipt_income --check
python3 scripts/migration/migration_asset_catalog_verify.py --asset-root migration_assets --catalog migration_assets/manifest/migration_asset_catalog_v1.json --check
python3 scripts/migration/migration_asset_bus.py --verify-only --check
git diff --check
```
