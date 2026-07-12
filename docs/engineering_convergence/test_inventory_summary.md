# Test Inventory Summary

Generated from `test_inventory.csv`.

## Totals

- Total assets: `1120`
- Review queue: `4`
- Unknown runtime: `3`
- Long-running assets: `331`
- Manual gate review: `4`
- Aggregate-covered assets: `81`
- PR dedupe candidates: `707`

## By Layer

| Layer | Count |
| --- | ---: |
| governance | 347 |
| contract | 275 |
| data_migration | 217 |
| unit | 149 |
| odoo_integration | 56 |
| e2e | 38 |
| security | 20 |
| frontend_acceptance | 17 |
| gate | 1 |

## By Decision Gate

| Decision Gate | Count |
| --- | ---: |
| pr_candidate | 784 |
| integration_candidate | 292 |
| release_candidate | 36 |
| manual_review | 4 |
| release_required | 2 |
| pr_required | 1 |
| integration_required | 1 |

## By Disposition

| Disposition | Count |
| --- | ---: |
| deduplicate_before_required | 707 |
| keep_integration_or_release_only | 292 |
| covered_by_aggregate | 77 |
| keep_release_only | 36 |
| canonical_entry | 4 |
| review_or_archive | 4 |

## By Aggregate Target

| Aggregate Target | Count |
| --- | ---: |
| verify.unified_page_contract.lite | 54 |
| verify.unified_page_contract.v2 | 11 |
| verify.frontend.product.ready | 7 |
| verify.backend.contract.closure.mainline | 5 |
| make ci | 1 |
| make test.e2e | 1 |
| make test.odoo.integration | 1 |
| make test.e2e.fixed_data.odoo | 1 |

## By Runtime

| Runtime | Count |
| --- | ---: |
| <5m | 785 |
| 10-30m | 293 |
| 30-60m | 38 |
| unknown | 3 |
| 10-15m | 1 |

## By Owner

| Owner | Count |
| --- | ---: |
| architecture owner | 347 |
| platform owner | 275 |
| data owner | 217 |
| test owner | 150 |
| backend owner | 56 |
| qa owner | 38 |
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
| make | 4 |
| scripts/audit | 4 |
| scripts/diag | 4 |
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
| T-ASSET-034 | unit | `scripts/diag/fe_smoke.sh` |
| T-ASSET-036 | unit | `scripts/diag/test-frontend-changes.sh` |
| T-ASSET-037 | unit | `scripts/diag/test-menu-issue.sh` |

## PR Dedupe Candidate Sample

| ID | Layer | Entrypoint | Owner |
| --- | --- | --- | --- |
| T-ASSET-002 | frontend_acceptance | `frontend/apps/web/scripts/business_form_all_category_direct_acceptance.mjs` | frontend owner |
| T-ASSET-003 | frontend_acceptance | `frontend/apps/web/scripts/business_form_frontend_full_walk_acceptance.mjs` | frontend owner |
| T-ASSET-004 | frontend_acceptance | `frontend/apps/web/scripts/business_form_user_perspective_acceptance.mjs` | frontend owner |
| T-ASSET-005 | frontend_acceptance | `frontend/apps/web/scripts/business_form_user_perspective_summary_guard.mjs` | frontend owner |
| T-ASSET-006 | frontend_acceptance | `frontend/apps/web/scripts/config_workbench_operation_acceptance.mjs` | frontend owner |
| T-ASSET-007 | frontend_acceptance | `frontend/apps/web/scripts/config_workbench_operation_coverage_guard.mjs` | frontend owner |
| T-ASSET-008 | frontend_acceptance | `frontend/apps/web/scripts/config_workbench_operation_summary_guard.mjs` | frontend owner |
| T-ASSET-009 | frontend_acceptance | `frontend/apps/web/scripts/handling_entry_catalog_smoke.mjs` | frontend owner |
| T-ASSET-010 | contract | `frontend/apps/web/scripts/list_selection_contract_smoke.mjs` | platform owner |
| T-ASSET-011 | frontend_acceptance | `frontend/apps/web/scripts/low_code_business_config_acceptance.mjs` | frontend owner |
| T-ASSET-012 | frontend_acceptance | `frontend/apps/web/scripts/low_code_form_group_matrix_acceptance.mjs` | frontend owner |
| T-ASSET-015 | frontend_acceptance | `frontend/apps/web/scripts/low_code_global_stability_acceptance.mjs` | frontend owner |
| T-ASSET-016 | frontend_acceptance | `frontend/apps/web/scripts/low_code_menu_navigation_alignment_acceptance.mjs` | frontend owner |
| T-ASSET-017 | frontend_acceptance | `frontend/apps/web/scripts/product_navigation_boundary_acceptance.mjs` | frontend owner |
| T-ASSET-018 | frontend_acceptance | `frontend/apps/web/scripts/product_page_structure_guard.mjs` | frontend owner |
| T-ASSET-020 | frontend_acceptance | `frontend/apps/web/scripts/system_user_experience_shell_acceptance.mjs` | frontend owner |
| T-ASSET-021 | frontend_acceptance | `frontend/apps/web/scripts/system_user_experience_shell_summary_guard.mjs` | frontend owner |
| T-ASSET-022 | frontend_acceptance | `frontend/apps/web/scripts/user_visible_surface_visual_coverage_summary_guard.mjs` | frontend owner |
| T-ASSET-023 | governance | `scripts/audit/boundary_audit_smart_core.py` | architecture owner |
| T-ASSET-024 | governance | `scripts/audit/scene_config_audit.js` | architecture owner |
| T-ASSET-027 | governance | `scripts/ci/assert_audit_tp08.py` | architecture owner |
| T-ASSET-029 | governance | `scripts/ci/gate_audit.sh` | architecture owner |
| T-ASSET-030 | governance | `scripts/ci/gate_audit_tp08.sh` | architecture owner |
| T-ASSET-031 | unit | `scripts/ci/generate_e2e_journey_matrix.py` | test owner |
| T-ASSET-032 | unit | `scripts/ci/generate_test_inventory.py` | test owner |
| T-ASSET-033 | unit | `scripts/ci/summarize_test_inventory.py` | test owner |
| T-ASSET-261 | contract | `scripts/ops/contract_product_acceptance_policy_restore.py` | platform owner |
| T-ASSET-267 | contract | `scripts/ops/direct_general_contract_input_tax_to_output_invoice_registration_sync.py` | platform owner |
| T-ASSET-268 | contract | `scripts/ops/engineering_progress_income_visible_contract_sync.py` | platform owner |
| T-ASSET-269 | contract | `scripts/ops/formal_list_surface_test_contract_cleanup.py` | platform owner |
| T-ASSET-273 | contract | `scripts/ops/operation_strategy_contract_surface_backfill.py` | platform owner |
| T-ASSET-274 | contract | `scripts/ops/output_invoice_application_visible_contract_sync.py` | platform owner |
| T-ASSET-275 | contract | `scripts/ops/output_invoice_registration_visible_contract_sync.py` | platform owner |
| T-ASSET-279 | contract | `scripts/ops/partner_payment_visible_contract_sync.py` | platform owner |
| T-ASSET-282 | contract | `scripts/ops/settlement_contract_surface_backfill.py` | platform owner |
| T-ASSET-286 | contract | `scripts/ops/validate_contract_business_categories.sh` | platform owner |
| T-ASSET-297 | contract | `scripts/verify/action_default_group_contract_audit.py` | platform owner |
| T-ASSET-298 | contract | `scripts/verify/action_view_orchestration_contract_shape_smoke.js` | platform owner |
| T-ASSET-299 | governance | `scripts/verify/app_config_engine_boundary_guard.py` | architecture owner |
| T-ASSET-300 | governance | `scripts/verify/application_form_required_marker_audit.py` | architecture owner |
| T-ASSET-303 | security | `scripts/verify/auth_xpath_guard.sh` | security owner |
| T-ASSET-304 | unit | `scripts/verify/auto_degrade_smoke_report.py` | test owner |
| T-ASSET-305 | governance | `scripts/verify/backend_architecture_full_report_guard.py` | architecture owner |
| T-ASSET-306 | contract | `scripts/verify/backend_architecture_full_report_guard_schema_guard.py` | platform owner |
| T-ASSET-307 | contract | `scripts/verify/backend_architecture_full_report_schema_guard.py` | platform owner |
| T-ASSET-308 | governance | `scripts/verify/backend_boundary_guard.py` | architecture owner |
| T-ASSET-309 | governance | `scripts/verify/backend_business_fact_model_audit.py` | architecture owner |
| T-ASSET-310 | contract | `scripts/verify/backend_contract_boundary_guard.py` | platform owner |
| T-ASSET-316 | governance | `scripts/verify/backend_evidence_manifest_guard.py` | architecture owner |
| T-ASSET-317 | contract | `scripts/verify/backend_evidence_manifest_schema_guard.py` | platform owner |
| T-ASSET-318 | governance | `scripts/verify/baseline_freeze_guard.py` | architecture owner |
| T-ASSET-319 | governance | `scripts/verify/baseline_policy_integrity_guard.py` | architecture owner |
| T-ASSET-320 | governance | `scripts/verify/boundary_import_guard.py` | architecture owner |
| T-ASSET-321 | contract | `scripts/verify/boundary_import_guard_schema_guard.py` | platform owner |
| T-ASSET-322 | governance | `scripts/verify/boundary_import_guard_strict_guard.py` | architecture owner |
| T-ASSET-323 | governance | `scripts/verify/business_action_coverage_audit.py` | architecture owner |
| T-ASSET-324 | governance | `scripts/verify/business_capability_baseline_report_guard.py` | architecture owner |
| T-ASSET-325 | contract | `scripts/verify/business_capability_baseline_report_schema_guard.py` | platform owner |
| T-ASSET-326 | governance | `scripts/verify/business_category_dictionary_audit.py` | architecture owner |
| T-ASSET-328 | contract | `scripts/verify/business_config_contract_snapshot.py` | platform owner |
| T-ASSET-329 | unit | `scripts/verify/business_config_form_layout_acceptance.js` | test owner |
| T-ASSET-330 | governance | `scripts/verify/business_config_guard_inventory.py` | architecture owner |
| T-ASSET-332 | governance | `scripts/verify/business_config_user_language_guard.py` | architecture owner |
| T-ASSET-333 | governance | `scripts/verify/business_core_journey_guard.py` | architecture owner |
| T-ASSET-335 | unit | `scripts/verify/business_document_state_policy_switch_smoke.py` | test owner |
| T-ASSET-336 | governance | `scripts/verify/business_fact_backfill_audit.py` | architecture owner |
| T-ASSET-338 | governance | `scripts/verify/business_flow_closure_audit.py` | architecture owner |
| T-ASSET-339 | governance | `scripts/verify/business_form_historical_logic_coverage_audit.py` | architecture owner |
| T-ASSET-340 | governance | `scripts/verify/business_form_interaction_capability_audit.py` | architecture owner |
| T-ASSET-341 | governance | `scripts/verify/business_form_policy_coverage_audit.py` | architecture owner |
| T-ASSET-342 | governance | `scripts/verify/business_form_policy_field_hit_audit.py` | architecture owner |
| T-ASSET-343 | governance | `scripts/verify/business_form_productization_audit.py` | architecture owner |
| T-ASSET-344 | governance | `scripts/verify/business_form_productization_standard_guard.py` | architecture owner |
| T-ASSET-345 | unit | `scripts/verify/business_form_user_perspective_acceptance.py` | test owner |
| T-ASSET-346 | governance | `scripts/verify/business_list_config_boundary_audit.py` | architecture owner |
| T-ASSET-348 | governance | `scripts/verify/business_shape_assembly_guard.py` | architecture owner |
| T-ASSET-349 | contract | `scripts/verify/capability_core_health_report_schema_guard.py` | platform owner |
| T-ASSET-350 | governance | `scripts/verify/capability_dormant_explain_guard.py` | architecture owner |
| T-ASSET-351 | governance | `scripts/verify/capability_provider_guard.py` | architecture owner |
| T-ASSET-352 | unit | `scripts/verify/capability_registry_smoke.py` | test owner |
| ... | ... | 627 more | ... |

## Dedupe Hotspots

| Family | Count |
| --- | ---: |
| `scripts/verify/scene_action_surface` | 5 |
| `scripts/verify/company_contractor_responsibility` | 4 |
| `scripts/verify/lowcode_customer_config` | 4 |
| `scripts/verify/scene_base_contract` | 4 |
| `frontend/apps/web/scripts/config_workbench_operation` | 3 |
| `scripts/verify/backend_architecture_full` | 3 |
| `scripts/verify/fe_scene_contract` | 3 |
| `scripts/verify/fe_scene_package` | 3 |
| `scripts/verify/form_structure_contract` | 3 |
| `scripts/verify/frontend_page_block` | 3 |
| `scripts/verify/grouped_governance_brief` | 3 |
| `scripts/verify/grouped_governance_trend` | 3 |
| `scripts/verify/material_settlement_payment` | 3 |
| `scripts/verify/payment_request_approval` | 3 |
| `scripts/verify/release_v2_0` | 3 |
| `scripts/verify/scene_contract_coverage` | 3 |
| `scripts/verify/scene_validation_recovery` | 3 |
| `scripts/verify/smart_core_minimum` | 3 |
| `scripts/verify/unified_page_contract` | 3 |
| `frontend/apps/web/scripts/business_form_user` | 2 |
| `frontend/apps/web/scripts/system_user_experience` | 2 |
| `scripts/verify/backend_evidence_manifest` | 2 |
| `scripts/verify/boundary_import_guard` | 2 |
| `scripts/verify/business_capability_baseline` | 2 |
| `scripts/verify/business_form_policy` | 2 |
| `scripts/verify/business_form_productization` | 2 |
| `scripts/verify/contract_assembler_semantic` | 2 |
| `scripts/verify/contract_business_category` | 2 |
| `scripts/verify/fe_ar_ap` | 2 |
| `scripts/verify/fe_list_shell` | 2 |
