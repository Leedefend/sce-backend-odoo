# Test Inventory Summary

Generated from `test_inventory.csv`.

## Totals

- Total assets: `1119`
- Review queue: `4`
- Unknown runtime: `33`
- Long-running assets: `144`

## By Layer

| Layer | Count |
| --- | ---: |
| contract | 441 |
| governance | 347 |
| unit | 149 |
| odoo_integration | 56 |
| data_migration | 51 |
| e2e | 37 |
| security | 20 |
| frontend_acceptance | 17 |
| gate | 1 |

## By Runtime

| Runtime | Count |
| --- | ---: |
| <5m | 941 |
| 10-30m | 106 |
| 30-60m | 38 |
| unknown | 33 |
| 10-15m | 1 |

## By Owner

| Owner | Count |
| --- | ---: |
| platform owner | 441 |
| architecture owner | 347 |
| test owner | 150 |
| backend owner | 56 |
| data owner | 51 |
| qa owner | 37 |
| security owner | 20 |
| frontend owner | 17 |

## By Directory

| Directory | Count |
| --- | ---: |
| scripts/verify | 820 |
| scripts/migration | 215 |
| scripts/ops | 37 |
| frontend/apps/web/scripts | 22 |
| scripts/ci | 7 |
| scripts/e2e | 5 |
| scripts/audit | 4 |
| scripts/diag | 4 |
| make | 3 |
| scripts/prod | 2 |

## Review Queue

| ID | Layer | Entrypoint | Reason |
| --- | --- | --- | --- |
| T-ASSET-034 | unit | `scripts/diag/fe_smoke.sh` | status=review |
| T-ASSET-035 | unit | `scripts/diag/test-default-menu.py` | status=review |
| T-ASSET-036 | unit | `scripts/diag/test-frontend-changes.sh` | status=review |
| T-ASSET-037 | unit | `scripts/diag/test-menu-issue.sh` | status=review |

## Unknown Runtime Assets

| ID | Layer | Entrypoint |
| --- | --- | --- |
| T-ASSET-025 | unit | `scripts/audit/smoke_business_full.sh` |
| T-ASSET-026 | security | `scripts/audit/smoke_role_matrix.sh` |
| T-ASSET-028 | unit | `scripts/ci/ensure_testdeps.sh` |
| T-ASSET-029 | governance | `scripts/ci/gate_audit.sh` |
| T-ASSET-030 | governance | `scripts/ci/gate_audit_tp08.sh` |
| T-ASSET-034 | unit | `scripts/diag/fe_smoke.sh` |
| T-ASSET-036 | unit | `scripts/diag/test-frontend-changes.sh` |
| T-ASSET-037 | unit | `scripts/diag/test-menu-issue.sh` |
| T-ASSET-284 | contract | `scripts/ops/validate_company_contractor_responsibility_context.sh` |
| T-ASSET-285 | contract | `scripts/ops/validate_company_contractor_responsibility_summary.sh` |
| T-ASSET-286 | contract | `scripts/ops/validate_contract_business_categories.sh` |
| T-ASSET-287 | contract | `scripts/ops/validate_contract_business_category_binding.sh` |
| T-ASSET-288 | contract | `scripts/ops/validate_contract_settlement_payment_closure.sh` |
| T-ASSET-290 | contract | `scripts/ops/validate_income_contract_receipt_invoice_closure.sh` |
| T-ASSET-291 | contract | `scripts/ops/validate_operation_strategy_contract_surface.sh` |
| T-ASSET-293 | contract | `scripts/ops/validate_settlement_contract_surface.sh` |
| T-ASSET-294 | contract | `scripts/ops/validate_subcontract_request_contract_anchor.sh` |
| T-ASSET-303 | security | `scripts/verify/auth_xpath_guard.sh` |
| T-ASSET-354 | unit | `scripts/verify/capability_smoke.sh` |
| T-ASSET-373 | contract | `scripts/verify/contract_drift_guard.sh` |
| T-ASSET-386 | contract | `scripts/verify/contract_preflight_resume.sh` |
| T-ASSET-413 | contract | `scripts/verify/e2e_contract_guard.sh` |
| T-ASSET-414 | governance | `scripts/verify/e2e_scene_guard.sh` |
| T-ASSET-419 | governance | `scripts/verify/extension_modules_guard.sh` |
| T-ASSET-558 | contract | `scripts/verify/form_structure_contract_runtime_audit.sh` |
| T-ASSET-565 | governance | `scripts/verify/form_view_scope_action_projection_audit.sh` |
| T-ASSET-715 | unit | `scripts/verify/marketplace_smoke.sh` |
| T-ASSET-741 | governance | `scripts/verify/native_parser_capability_audit.sh` |
| T-ASSET-755 | unit | `scripts/verify/ops_batch_smoke.sh` |
| T-ASSET-802 | governance | `scripts/verify/prod_guard_smoke.sh` |
| T-ASSET-887 | unit | `scripts/verify/scene_admin_smoke.sh` |
| T-ASSET-982 | unit | `scripts/verify/subscription_smoke.sh` |
| T-ASSET-1004 | governance | `scripts/verify/test_seed_dependency_guard.sh` |
