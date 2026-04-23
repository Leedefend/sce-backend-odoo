# Legacy Expense Deposit Asset Package v1

Status: `PASS`

This batch turns project-anchored positive-amount legacy expense, financial outflow, and deposit facts into replayable XML assets for `sc.legacy.expense.deposit.fact`.

## Scope

- package id: `legacy_expense_deposit_sc_v1`
- lane: `legacy_expense_deposit`
- layer: `30_relation`
- target model: `sc.legacy.expense.deposit.fact`
- XML: `migration_assets/30_relation/legacy_expense_deposit/legacy_expense_deposit_v1.xml`
- manifest: `migration_assets/manifest/legacy_expense_deposit_asset_manifest_v1.json`
- DB writes: `0`
- Odoo shell: `false`

## Result

- raw source rows: `14330`
- loadable XML records: `11167`
- blocked rows: `3163`
- migration asset bus package count after registration: `19`

## Included Business Facts

| Family | Rows |
|---|---:|
| pay_guarantee_deposit | 2871 |
| company_financial_outflow | 2656 |
| pay_guarantee_deposit_refund | 1872 |
| received_guarantee_deposit_register | 1531 |
| expense_reimbursement | 1432 |
| received_guarantee_deposit_refund | 805 |

## Direction Counts

| Direction | Rows |
|---|---:|
| outflow | 6959 |
| inflow_or_refund | 2677 |
| inflow | 1531 |

## Partner Handling

| Partner route | Rows |
|---|---:|
| partner_missing | 4991 |
| partner_text_only | 4936 |
| partner_ref | 1240 |

The new model allows a partner to be a company or an individual. When the old partner id resolves to an assetized `res.partner`, XML writes `partner_id` as a stable external id. Otherwise the package preserves `legacy_partner_id` and `legacy_partner_name` as source facts.

## Blocked Reasons

| Reason | Rows |
|---|---:|
| amount_not_positive_or_missing | 2504 |
| deleted | 381 |
| project_not_assetized | 343 |
| missing_project_id | 3 |

Rows may have more than one blocked reason, so reason counts are diagnostic rather than a unique blocked-row total.

## Boundary

This package preserves finance-adjacent historical business facts only.

Excluded from this batch:

- `account.move`
- settlement state
- payment ledger state
- runtime approval state
- database integer-id dependencies

## Verification

Commands passed:

```bash
python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-15-MIGRATION-EXPENSE-DEPOSIT-ASSET-PACKAGE.yaml
python3 -m py_compile scripts/migration/legacy_expense_deposit_asset_generator.py scripts/migration/legacy_expense_deposit_asset_verify.py scripts/migration/migration_asset_bus.py scripts/migration/migration_asset_catalog_verify.py
python3 scripts/migration/legacy_expense_deposit_asset_generator.py --asset-root migration_assets --check
python3 scripts/migration/legacy_expense_deposit_asset_verify.py --asset-root migration_assets --lane legacy_expense_deposit --check
python3 scripts/migration/migration_asset_catalog_verify.py --asset-root migration_assets --catalog migration_assets/manifest/migration_asset_catalog_v1.json --check
python3 scripts/migration/migration_asset_bus.py --verify-only --check
git diff --check
```
