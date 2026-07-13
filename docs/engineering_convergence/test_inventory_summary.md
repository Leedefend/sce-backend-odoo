# Test Inventory Summary

Generated from `test_inventory.csv`.

## Totals

- Total assets: `1117`
- Review queue: `4`
- Unknown runtime: `3`
- Long-running assets: `330`
- Manual gate review: `4`
- Aggregate-covered assets: `230`
- PR dedupe candidates: `557`

## By Layer

| Layer | Count |
| --- | ---: |
| governance | 344 |
| contract | 276 |
| data_migration | 217 |
| unit | 149 |
| odoo_integration | 55 |
| e2e | 38 |
| security | 20 |
| frontend_acceptance | 16 |
| gate | 2 |

## By Decision Gate

| Decision Gate | Count |
| --- | ---: |
| pr_candidate | 781 |
| integration_candidate | 291 |
| release_candidate | 36 |
| manual_review | 4 |
| release_required | 2 |
| local_iteration | 1 |
| pr_required | 1 |
| integration_required | 1 |

## By Disposition

| Disposition | Count |
| --- | ---: |
| deduplicate_before_required | 557 |
| keep_integration_or_release_only | 290 |
| covered_by_aggregate | 225 |
| keep_release_only | 36 |
| canonical_entry | 5 |
| review_or_archive | 4 |

## By Aggregate Target

| Aggregate Target | Count |
| --- | ---: |
| verify.unified_page_contract.lite | 54 |
| verify.scene.runtime_boundary.gate | 17 |
| verify.unified_page_contract.v2 | 11 |
| verify.frontend.product.ready | 7 |
| verify.system_user_experience.full_browser | 5 |
| verify.backend.contract.closure.mainline | 5 |
| verify.finance_interfund.position.all | 5 |
| verify.form_structure.contract | 4 |
| verify.lowcode_config.customer_module_asset.pipeline | 4 |
| verify.backend.architecture.full.report.guard.schema.guard | 3 |
| verify.boundary.import_guard.strict.guard | 3 |
| verify.frontend.grouped_drift_summary.baseline.guard | 3 |
| verify.frontend.grouped_governance_brief.baseline.guard | 3 |
| verify.frontend.grouped_governance_trend_consistency.baseline.guard | 3 |
| verify.business_capability.productization_p1 | 3 |
| verify.portal.payment_request_approval_all_smoke.container | 3 |
| verify.release.v2_0_0.governance.guard | 3 |
| verify.contract.scene_coverage.guard | 3 |
| verify.smart_core.minimum_surface | 3 |
| verify.business_config.config_workbench_operation_quick | 2 |
| verify.backend.evidence.manifest.guard | 2 |
| verify.business.capability_baseline.guard | 2 |
| verify.business_form.productization.audit | 2 |
| verify.contract.assembler.semantic.schema.guard | 2 |
| verify.frontend.quick.gate | 2 |
| verify.grouped.governance.bundle | 2 |
| verify.intent.canonical_alias.snapshot.guard | 2 |
| verify.native_view.semantic_page | 2 |
| verify.non_demo_data_contamination | 2 |
| verify.e2e.ops_batch_smoke | 2 |
| verify.portal.entry_registry_quality_guard | 2 |
| verify.product.delivery.governance_truth | 2 |
| verify.project.dashboard.contract | 2 |
| verify.project.dashboard.snapshot | 2 |
| verify.project.management.acceptance | 2 |
| verify.release.capability.audit.schema.guard | 2 |
| verify.e2e.scene_admin | 2 |
| verify.e2e.subscription_smoke | 2 |
| verify.formal_business.release_gate | 2 |
| make ci.local.quick | 1 |
| make ci | 1 |
| make test.e2e | 1 |
| make test.odoo.integration | 1 |
| make test.e2e.fixed_data.odoo | 1 |
| verify.business_config.config_workbench_operation_acceptance | 1 |
| verify.portal.ar_ap_company_summary_smoke.container | 1 |
| verify.portal.ar_ap_project_summary_smoke.container | 1 |
| verify.portal.list_shell_no_meta_smoke.container | 1 |
| verify.portal.list_shell_title_smoke.container | 1 |
| verify.portal.menu_scene_key_smoke.container | 1 |
| verify.menu.scene_resolve.container | 1 |
| verify.portal.scene_governance_action_strict.container | 1 |
| verify.portal.scene_package_ui_smoke.container | 1 |
| verify.portal.scene_auto_degrade_notify_strict.container | 1 |
| verify.portal.scene_auto_degrade_strict.container | 1 |
| scene.contract.export | 1 |
| verify.portal.scene_contract_export_smoke.container | 1 |
| verify.portal.scene_contract_smoke.container | 1 |
| verify.portal.scene_health_contract_smoke.container | 1 |
| verify.portal.scene_health_pagination_smoke.container | 1 |
| verify.portal.scene_package_dry_run_smoke.container | 1 |
| verify.portal.scene_observability_strict.container | 1 |
| verify.portal.scene_package_installed_smoke.container | 1 |
| verify.portal.scene_registry | 1 |
| verify.portal.view_contract_coverage_smoke.container | 1 |
| verify.portal.view_contract_shape.container | 1 |
| verify.formal_list_surface.no_test_placeholder_guard | 1 |
| verify.frontend.page_block_registry_guard | 1 |
| verify.frontend.page_block_renderer_smoke | 1 |
| verify.frontend.page_block_visual_snapshot_guard | 1 |
| verify.lowcode_config.customer_module_asset.release_hardening.guard | 1 |
| verify.delivery.material.cross_document_progress | 1 |
| verify.p1.daily_business_visible_contract.audit | 1 |
| verify.page_contract.role_orchestration_variance.guard | 1 |
| verify.page_contract.role_strategy_provider_split.guard | 1 |
| verify.role.capability_floor.guard | 1 |
| verify.role.capability_floor.prod_like.schema.guard | 1 |
| migration.assets.user_acceptance_manifest_guard.evidence | 1 |
| migration.assets.user_acceptance_online_probe | 1 |
| migration.assets.scbsly_direct_project_menu_probe | 1 |
| verify.scene.provider.registry.consumer.guard | 1 |
| verify.scene.provider.registry.guard | 1 |
| verify.scene.delivery.readiness | 1 |
| verify.smart_core.boundary_guard | 1 |
| verify.unified_page_contract.v2.harmony_h5_compile_acceptance.host | 1 |
| verify.unified_page_contract.v2.regression_audit.host | 1 |
| verify.unified_page_contract.v2.web_visual_acceptance.host | 1 |

## By Runtime

| Runtime | Count |
| --- | ---: |
| <5m | 783 |
| 10-30m | 292 |
| 30-60m | 38 |
| unknown | 3 |
| 10-15m | 1 |

## By Owner

| Owner | Count |
| --- | ---: |
| architecture owner | 344 |
| platform owner | 276 |
| data owner | 217 |
| test owner | 150 |
| backend owner | 55 |
| qa owner | 38 |
| security owner | 20 |
| frontend owner | 17 |

## By Directory

| Directory | Count |
| --- | ---: |
| scripts/verify | 817 |
| scripts/migration | 215 |
| scripts/ops | 37 |
| frontend/apps/web/scripts | 20 |
| scripts/ci | 8 |
| make | 5 |
| scripts/e2e | 5 |
| scripts/audit | 4 |
| scripts/diag | 4 |
| scripts/prod | 2 |

## Review Queue

| ID | Layer | Entrypoint | Reason |
| --- | --- | --- | --- |
| T-ASSET-033 | unit | `scripts/diag/fe_smoke.sh` | status=review |
| T-ASSET-034 | unit | `scripts/diag/test-default-menu.py` | status=review |
| T-ASSET-035 | unit | `scripts/diag/test-frontend-changes.sh` | status=review |
| T-ASSET-036 | unit | `scripts/diag/test-menu-issue.sh` | status=review |

## Unknown Runtime Assets

| ID | Layer | Entrypoint |
| --- | --- | --- |
| T-ASSET-033 | unit | `scripts/diag/fe_smoke.sh` |
| T-ASSET-035 | unit | `scripts/diag/test-frontend-changes.sh` |
| T-ASSET-036 | unit | `scripts/diag/test-menu-issue.sh` |

## PR Dedupe Candidate Sample

| ID | Layer | Entrypoint | Owner |
| --- | --- | --- | --- |
| T-ASSET-001 | frontend_acceptance | `frontend/apps/web/scripts/business_form_all_category_direct_acceptance.mjs` | frontend owner |
| T-ASSET-002 | frontend_acceptance | `frontend/apps/web/scripts/business_form_frontend_full_walk_acceptance.mjs` | frontend owner |
| T-ASSET-008 | frontend_acceptance | `frontend/apps/web/scripts/handling_entry_catalog_smoke.mjs` | frontend owner |
| T-ASSET-009 | contract | `frontend/apps/web/scripts/list_selection_contract_smoke.mjs` | platform owner |
| T-ASSET-010 | frontend_acceptance | `frontend/apps/web/scripts/low_code_business_config_acceptance.mjs` | frontend owner |
| T-ASSET-011 | frontend_acceptance | `frontend/apps/web/scripts/low_code_form_group_matrix_acceptance.mjs` | frontend owner |
| T-ASSET-014 | frontend_acceptance | `frontend/apps/web/scripts/low_code_global_stability_acceptance.mjs` | frontend owner |
| T-ASSET-015 | frontend_acceptance | `frontend/apps/web/scripts/low_code_menu_navigation_alignment_acceptance.mjs` | frontend owner |
| T-ASSET-016 | frontend_acceptance | `frontend/apps/web/scripts/product_navigation_boundary_acceptance.mjs` | frontend owner |
| T-ASSET-017 | frontend_acceptance | `frontend/apps/web/scripts/product_page_structure_guard.mjs` | frontend owner |
| T-ASSET-021 | governance | `scripts/audit/boundary_audit_smart_core.py` | architecture owner |
| T-ASSET-022 | governance | `scripts/audit/scene_config_audit.js` | architecture owner |
| T-ASSET-025 | governance | `scripts/ci/assert_audit_tp08.py` | architecture owner |
| T-ASSET-027 | governance | `scripts/ci/gate_audit.sh` | architecture owner |
| T-ASSET-028 | governance | `scripts/ci/gate_audit_tp08.sh` | architecture owner |
| T-ASSET-029 | unit | `scripts/ci/generate_e2e_journey_matrix.py` | test owner |
| T-ASSET-030 | unit | `scripts/ci/generate_test_inventory.py` | test owner |
| T-ASSET-031 | unit | `scripts/ci/summarize_test_inventory.py` | test owner |
| T-ASSET-032 | contract | `scripts/ci/verify_contract_form_split_evidence.py` | platform owner |
| T-ASSET-260 | contract | `scripts/ops/contract_product_acceptance_policy_restore.py` | platform owner |
| T-ASSET-266 | contract | `scripts/ops/direct_general_contract_input_tax_to_output_invoice_registration_sync.py` | platform owner |
| T-ASSET-267 | contract | `scripts/ops/engineering_progress_income_visible_contract_sync.py` | platform owner |
| T-ASSET-268 | contract | `scripts/ops/formal_list_surface_test_contract_cleanup.py` | platform owner |
| T-ASSET-272 | contract | `scripts/ops/operation_strategy_contract_surface_backfill.py` | platform owner |
| T-ASSET-273 | contract | `scripts/ops/output_invoice_application_visible_contract_sync.py` | platform owner |
| T-ASSET-274 | contract | `scripts/ops/output_invoice_registration_visible_contract_sync.py` | platform owner |
| T-ASSET-278 | contract | `scripts/ops/partner_payment_visible_contract_sync.py` | platform owner |
| T-ASSET-281 | contract | `scripts/ops/settlement_contract_surface_backfill.py` | platform owner |
| T-ASSET-285 | contract | `scripts/ops/validate_contract_business_categories.sh` | platform owner |
| T-ASSET-296 | contract | `scripts/verify/action_default_group_contract_audit.py` | platform owner |
| T-ASSET-297 | contract | `scripts/verify/action_view_orchestration_contract_shape_smoke.js` | platform owner |
| T-ASSET-298 | governance | `scripts/verify/app_config_engine_boundary_guard.py` | architecture owner |
| T-ASSET-299 | governance | `scripts/verify/application_form_required_marker_audit.py` | architecture owner |
| T-ASSET-302 | security | `scripts/verify/auth_xpath_guard.sh` | security owner |
| T-ASSET-303 | unit | `scripts/verify/auto_degrade_smoke_report.py` | test owner |
| T-ASSET-307 | governance | `scripts/verify/backend_boundary_guard.py` | architecture owner |
| T-ASSET-308 | governance | `scripts/verify/backend_business_fact_model_audit.py` | architecture owner |
| T-ASSET-309 | contract | `scripts/verify/backend_contract_boundary_guard.py` | platform owner |
| T-ASSET-317 | governance | `scripts/verify/baseline_freeze_guard.py` | architecture owner |
| T-ASSET-318 | governance | `scripts/verify/baseline_policy_integrity_guard.py` | architecture owner |
| T-ASSET-322 | governance | `scripts/verify/business_action_coverage_audit.py` | architecture owner |
| T-ASSET-325 | governance | `scripts/verify/business_category_dictionary_audit.py` | architecture owner |
| T-ASSET-327 | contract | `scripts/verify/business_config_contract_snapshot.py` | platform owner |
| T-ASSET-328 | unit | `scripts/verify/business_config_form_layout_acceptance.js` | test owner |
| T-ASSET-329 | governance | `scripts/verify/business_config_guard_inventory.py` | architecture owner |
| T-ASSET-331 | governance | `scripts/verify/business_config_user_language_guard.py` | architecture owner |
| T-ASSET-332 | governance | `scripts/verify/business_core_journey_guard.py` | architecture owner |
| T-ASSET-334 | unit | `scripts/verify/business_document_state_policy_switch_smoke.py` | test owner |
| T-ASSET-335 | governance | `scripts/verify/business_fact_backfill_audit.py` | architecture owner |
| T-ASSET-337 | governance | `scripts/verify/business_flow_closure_audit.py` | architecture owner |
| T-ASSET-338 | governance | `scripts/verify/business_form_historical_logic_coverage_audit.py` | architecture owner |
| T-ASSET-339 | governance | `scripts/verify/business_form_interaction_capability_audit.py` | architecture owner |
| T-ASSET-340 | governance | `scripts/verify/business_form_policy_coverage_audit.py` | architecture owner |
| T-ASSET-341 | governance | `scripts/verify/business_form_policy_field_hit_audit.py` | architecture owner |
| T-ASSET-344 | unit | `scripts/verify/business_form_user_perspective_acceptance.py` | test owner |
| T-ASSET-345 | governance | `scripts/verify/business_list_config_boundary_audit.py` | architecture owner |
| T-ASSET-347 | governance | `scripts/verify/business_shape_assembly_guard.py` | architecture owner |
| T-ASSET-348 | contract | `scripts/verify/capability_core_health_report_schema_guard.py` | platform owner |
| T-ASSET-349 | governance | `scripts/verify/capability_dormant_explain_guard.py` | architecture owner |
| T-ASSET-350 | governance | `scripts/verify/capability_provider_guard.py` | architecture owner |
| T-ASSET-351 | unit | `scripts/verify/capability_registry_smoke.py` | test owner |
| T-ASSET-352 | unit | `scripts/verify/capability_smoke.py` | test owner |
| T-ASSET-355 | contract | `scripts/verify/company_contractor_responsibility_context_audit.py` | platform owner |
| T-ASSET-360 | governance | `scripts/verify/company_operation_summary_source_audit.py` | architecture owner |
| T-ASSET-361 | governance | `scripts/verify/complexity_guard.py` | architecture owner |
| T-ASSET-362 | contract | `scripts/verify/construction_contract_history_value_gap_probe.py` | platform owner |
| T-ASSET-363 | governance | `scripts/verify/construction_diary_visible_fields_audit.py` | architecture owner |
| T-ASSET-364 | governance | `scripts/verify/construction_product_menu_release_audit.py` | architecture owner |
| T-ASSET-365 | contract | `scripts/verify/contract_api_mode_smoke.py` | platform owner |
| T-ASSET-368 | contract | `scripts/verify/contract_business_category_action_audit.py` | platform owner |
| T-ASSET-369 | contract | `scripts/verify/contract_business_category_binding_audit.py` | platform owner |
| T-ASSET-370 | contract | `scripts/verify/contract_catalog_determinism_guard.py` | platform owner |
| T-ASSET-371 | contract | `scripts/verify/contract_compat_report.py` | platform owner |
| T-ASSET-372 | contract | `scripts/verify/contract_drift_guard.sh` | platform owner |
| T-ASSET-373 | contract | `scripts/verify/contract_envelope_guard.py` | platform owner |
| T-ASSET-374 | contract | `scripts/verify/contract_evidence_guard.py` | platform owner |
| T-ASSET-375 | contract | `scripts/verify/contract_evidence_schema_guard.py` | platform owner |
| T-ASSET-376 | contract | `scripts/verify/contract_form_handling_policy_audit.py` | platform owner |
| T-ASSET-377 | contract | `scripts/verify/contract_form_lowcode_orchestration_smoke.js` | platform owner |
| T-ASSET-378 | contract | `scripts/verify/contract_form_save_payload_builder_guard.py` | platform owner |
| ... | ... | 477 more | ... |

## Dedupe Hotspots

| Family | Count |
| --- | ---: |
| `scripts/verify/business_form_policy` | 2 |
| `scripts/verify/contract_business_category` | 2 |
| `scripts/verify/form_m2_payment` | 2 |
| `scripts/verify/form_m3_purchase` | 2 |
| `scripts/verify/intent_smoke_utils` | 2 |
| `scripts/verify/material_business_category` | 2 |
| `scripts/verify/material_settlement_payment` | 2 |
| `frontend/apps/web/scripts/business_form_all` | 1 |
| `frontend/apps/web/scripts/business_form_frontend` | 1 |
| `frontend/apps/web/scripts/handling_entry_catalog` | 1 |
| `frontend/apps/web/scripts/list_selection_contract` | 1 |
| `frontend/apps/web/scripts/low_code_business` | 1 |
| `frontend/apps/web/scripts/low_code_form` | 1 |
| `frontend/apps/web/scripts/low_code_global` | 1 |
| `frontend/apps/web/scripts/low_code_menu` | 1 |
| `frontend/apps/web/scripts/product_navigation_boundary` | 1 |
| `frontend/apps/web/scripts/product_page_structure` | 1 |
| `scripts/audit/boundary_audit_smart` | 1 |
| `scripts/audit/scene_config` | 1 |
| `scripts/ci/assert_audit_tp08` | 1 |
| `scripts/ci/gate` | 1 |
| `scripts/ci/gate_audit_tp08` | 1 |
| `scripts/ci/generate_e2e_journey` | 1 |
| `scripts/ci/generate_test_inventory` | 1 |
| `scripts/ci/summarize_test_inventory` | 1 |
| `scripts/ci/verify_contract_form` | 1 |
| `scripts/ops/contract_product_acceptance` | 1 |
| `scripts/ops/direct_general_contract` | 1 |
| `scripts/ops/engineering_progress_income` | 1 |
| `scripts/ops/formal_list_surface` | 1 |

## Residual Dedupe Hotspot Disposition

| Family | Count | Owner | Gate Decision | Disposition |
| --- | ---: | --- | --- | --- |
| `scripts/verify/business_form_policy` | 2 | architecture owner | owner-reviewed PR candidates | Retain as explicit PR candidates; no confirmed aggregate gate covers both policy coverage and field-hit audit. |
| `scripts/verify/contract_business_category` | 2 | platform owner | owner-reviewed PR candidates | Retain as explicit PR candidates; action audit and binding audit are only wrapped by separate ops scripts. |
| `scripts/verify/form_m2_payment` | 2 | test owner | owner-reviewed PR candidates | Retain as explicit PR candidates; acceptance pair has no confirmed Make aggregate. |
| `scripts/verify/form_m3_purchase` | 2 | test owner | owner-reviewed PR candidates | Retain as explicit PR candidates; purchase/order-line acceptance pair has no confirmed Make aggregate. |
| `scripts/verify/intent_smoke_utils` | 2 | platform owner | helper debt, no aggregate gate | Retain as helper debt; utility modules are consumed by multiple smokes and should not be marked covered by one gate. |
| `scripts/verify/material_business_category` | 2 | architecture owner | owner-reviewed PR candidates | Retain as explicit PR candidates; action and binding audits are only wrapped by separate ops scripts. |
| `scripts/verify/material_settlement_payment` | 2 | architecture owner | owner-reviewed PR candidates | Retain as explicit PR candidates; approval policy and reversal audits are not covered by the traceability aggregate. |
