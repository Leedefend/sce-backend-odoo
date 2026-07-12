# ======================================================
# ==================== Dev Test ========================
# ======================================================
.PHONY: test test.safe
test: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/test/test.sh
test.safe: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/test/test_safe.sh

.PHONY: verify.e2e.contract verify.e2e.scene verify.e2e.scene_admin verify.e2e.capability_smoke verify.e2e.marketplace_smoke verify.e2e.subscription_smoke verify.e2e.ops_batch_smoke verify.capability.lint verify.frontend_api verify.frontend.intent_channel.guard verify.scene.legacy_endpoint.guard verify.scene.legacy_contract.guard verify.scene.legacy.contract.guard verify.scene.legacy_docs.guard verify.scene.legacy_auth.smoke verify.scene.legacy_deprecation.smoke verify.scene.legacy.bundle verify.scene.legacy.all verify.scene.runtime_boundary.gate verify.scene.contract_path.gate verify.intent.router.purity verify.scene.definition.semantics verify.scene.catalog.source.guard verify.scene.catalog.runtime_alignment.guard verify.scene.catalog.governance.guard verify.load_view.access.contract.guard verify.model.ui_dependency.guard verify.business.shape.guard verify.controller.delegate.guard verify.controller.allowlist.routes.guard verify.controller.route.policy.guard verify.controller.boundary.report verify.controller.boundary.baseline.guard verify.controller.boundary.guard verify.business.core_journey.guard verify.role.capability_floor.guard verify.role.capability_floor.prod_like verify.role.capability_floor.prod_like.schema.guard verify.contract.assembler.semantic.smoke verify.contract.assembler.semantic.strict verify.contract.assembler.semantic.schema.guard verify.project.form.contract.surface.guard verify.runtime.surface.dashboard.report verify.runtime.surface.dashboard.schema.guard verify.runtime.surface.dashboard.strict.guard verify.capability.core.health.report verify.capability.core.health.schema.guard verify.scene.contract.semantic.v2.guard verify.phase_next.evidence.bundle verify.phase_next.evidence.bundle.strict verify.business.capability_baseline.report verify.business.capability_baseline.report.schema.guard verify.business.capability_baseline.report.guard verify.business.capability_baseline.guard verify.contract.evidence.export verify.contract.evidence.schema.guard verify.contract.evidence.guard verify.baseline.policy_integrity.guard verify.scene.demo_leak.guard verify.contract.ordering.smoke verify.contract.catalog.determinism verify.contract.envelope verify.contract.envelope.guard verify.seed.demo.import_boundary.guard verify.seed.demo.isolation verify.boundary.guard verify.contract.snapshot verify.system_init.snapshot_equivalence verify.mode.filter verify.capability.schema verify.scene.schema verify.backend.architecture.full verify.backend.architecture.full.report verify.backend.architecture.full.report.schema.guard verify.backend.architecture.full.report.guard verify.backend.architecture.full.report.guard.schema.guard verify.backend.evidence.manifest verify.backend.evidence.manifest.schema.guard verify.backend.evidence.manifest.guard verify.extension_modules.guard verify.test_seed_dependency.guard verify.contract_drift.guard verify.intent.side_effect_policy_guard verify.baseline.freeze_guard verify.business.increment.preflight verify.business.increment.preflight.strict verify.business.increment.readiness verify.business.increment.readiness.strict verify.business.increment.readiness.brief verify.business.increment.readiness.brief.strict verify.docs.inventory verify.docs.links verify.docs.temp_guard verify.docs.contract_sync verify.docs.product_boundary verify.docs.all verify.boundary.import_guard verify.boundary.import_guard.schema.guard verify.boundary.import_guard.strict.guard verify.backend.boundary_guard verify.scene.provider.guard verify.capability.provider.guard verify.capability.registry.smoke verify.scene.hud.trace.smoke verify.scene.meta.trace.smoke verify.contract.governance.coverage verify.scene_capability.contract.guard verify.contract.governance.brief verify.contract.scene_coverage.brief verify.contract.scene_coverage.guard verify.contract.mode.smoke verify.contract.api.mode.smoke verify.contract.preflight verify.round.v0_6.mini verify.intent.capability.matrix.report verify.write_intent.permission.audit verify.scene.intent.matrix.report verify.etag.validation.report verify.auto_degrade.smoke.report verify.scene.drift.smoke.report verify.capability.orphan.report verify.platform.kernel.ready audit.intent.surface policy.apply.extension_modules policy.ensure.extension_modules
verify.e2e.contract: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/verify/e2e_contract_guard.sh
	@$(RUN_ENV) python3 scripts/e2e/e2e_contract_smoke.py
verify.e2e.scene: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/verify/e2e_scene_guard.sh
	@$(RUN_ENV) python3 scripts/e2e/e2e_scene_smoke.py
verify.e2e.scene_admin: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/verify/scene_admin_smoke.sh

verify.e2e.capability_smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/verify/capability_smoke.sh

verify.e2e.marketplace_smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/verify/marketplace_smoke.sh
verify.e2e.subscription_smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/verify/subscription_smoke.sh
verify.e2e.ops_batch_smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/verify/ops_batch_smoke.sh

.PHONY: verify.list_batch_action.closure_guard
verify.list_batch_action.closure_guard: guard.prod.forbid
	@python3 scripts/verify/list_batch_action_closure_guard.py

.PHONY: verify.user_delete_data.closure_guard
verify.user_delete_data.closure_guard: guard.prod.forbid
	@python3 scripts/verify/user_delete_data_closure_guard.py

.PHONY: verify.receipt_income_type_mapping.guard
verify.receipt_income_type_mapping.guard: guard.prod.forbid
	@python3 scripts/verify/receipt_income_type_mapping_guard.py

.PHONY: verify.payment_request_receipt_type.guard
verify.payment_request_receipt_type.guard: guard.prod.forbid
	@python3 scripts/verify/payment_request_receipt_type_guard.py

verify.capability.lint: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/verify/capability_lint.sh

.PHONY: verify.usage.product.clean
verify.usage.product.clean: guard.prod.forbid
	@python3 scripts/verify/usage_product_clean_guard.py

.PHONY: verify.platform_usage_handler_ownership.guard
verify.platform_usage_handler_ownership.guard: guard.prod.forbid
	@python3 scripts/verify/platform_usage_handler_ownership_guard.py

verify.frontend_api: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/frontend_api_smoke.py

.PHONY: verify.project.dashboard.contract
verify.project.dashboard.contract: guard.prod.forbid
	@python3 scripts/verify/project_management_contract_guard.py
	@python3 scripts/verify/project_dashboard_assembly_guard.py
	@python3 scripts/verify/project_dashboard_block_schema_guard.py
	@python3 scripts/verify/project_dashboard_block_payload_guard.py
	@python3 scripts/verify/project_dashboard_metric_semantics_guard.py
	@python3 scripts/verify/project_dashboard_intent_guard.py
	@python3 scripts/verify/project_dashboard_runtime_chain_guard.py
	@python3 scripts/verify/project_dashboard_project_id_order_guard.py
	@python3 -m py_compile addons/smart_construction_core/handlers/project_dashboard.py addons/smart_construction_core/services/project_dashboard_service.py addons/smart_construction_core/services/project_dashboard_builders/base.py addons/smart_construction_core/services/project_dashboard_builders/project_header_builder.py addons/smart_construction_core/services/project_dashboard_builders/project_metrics_builder.py addons/smart_construction_core/services/project_dashboard_builders/project_progress_builder.py addons/smart_construction_core/services/project_dashboard_builders/project_contract_builder.py addons/smart_construction_core/services/project_dashboard_builders/project_cost_builder.py addons/smart_construction_core/services/project_dashboard_builders/project_finance_builder.py addons/smart_construction_core/services/project_dashboard_builders/project_risk_builder.py
	@echo "[OK] verify.project.dashboard.contract done"

.PHONY: verify.workbench.extraction_hit_rate.report
verify.workbench.extraction_hit_rate.report: guard.prod.forbid
	@python3 scripts/verify/workbench_extraction_hit_rate_report.py
	@echo "[OK] verify.workbench.extraction_hit_rate.report done"

.PHONY: verify.user.entry.delivery.browser_acceptance
verify.user.entry.delivery.browser_acceptance: guard.prod.forbid
	@pnpm -C frontend/apps/web exec node ../../../scripts/verify/user_entry_delivery_browser_acceptance.js

.PHONY: verify.model_view.fact_layer.audit
verify.model_view.fact_layer.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MODEL_VIEW_AUDIT_LOGIN="$(or $(MODEL_VIEW_AUDIT_LOGIN),wutao)" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/model_view_fact_layer_audit.py

.PHONY: verify.model_view.standardization.plan
verify.model_view.standardization.plan: guard.prod.forbid verify.model_view.fact_layer.audit
	@python3 scripts/verify/model_view_standardization_plan.py

.PHONY: verify.project.dashboard.snapshot
verify.project.dashboard.snapshot: guard.prod.forbid
	@python3 scripts/verify/project_dashboard_contract_snapshot_export.py
	@python3 scripts/verify/project_dashboard_snapshot_schema_guard.py
	@python3 scripts/verify/project_dashboard_snapshot_freshness_guard.py
	@python3 scripts/verify/project_dashboard_evidence_export.py

.PHONY: verify.project.dashboard.evidence
verify.project.dashboard.evidence: guard.prod.forbid
	@python3 scripts/verify/project_dashboard_evidence_export.py

.PHONY: verify.project.management.productization
verify.project.management.productization: guard.prod.forbid verify.project.dashboard.contract verify.project.dashboard.snapshot
	@python3 scripts/verify/project_management_productization_flow_guard.py

.PHONY: verify.frontend.project_management.scene_bridge.guard
verify.frontend.project_management.scene_bridge.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_project_management_scene_bridge_guard.py

.PHONY: verify.frontend.scene_contract_v1.consumption.guard
verify.frontend.scene_contract_v1.consumption.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_scene_contract_v1_consumption_guard.py

.PHONY: verify.project.management.acceptance
verify.project.management.acceptance: guard.prod.forbid verify.project.management.productization verify.frontend.project_management.scene_bridge.guard
	@python3 scripts/verify/project_management_productization_acceptance_export.py

verify.frontend.intent_channel.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_intent_channel_guard.py

.PHONY: verify.frontend.contract_runtime.guard
verify.frontend.contract_runtime.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_contract_runtime_guard.py

.PHONY: verify.frontend.contract_route.guard
verify.frontend.contract_route.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_contract_route_guard.py

.PHONY: verify.frontend.contract_normalized_fields.guard
verify.frontend.contract_normalized_fields.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_contract_normalized_fields_guard.py

.PHONY: verify.frontend.contract_query_context.guard
verify.frontend.contract_query_context.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_contract_query_context_guard.py

.PHONY: verify.frontend.contract_record_layout.guard
verify.frontend.contract_record_layout.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_contract_record_layout_guard.py

.PHONY: verify.frontend.product.contract_consumption.guard
verify.frontend.product.contract_consumption.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_product_contract_consumption_guard.py

.PHONY: verify.frontend.runtime_navigation_hud.guard
verify.frontend.runtime_navigation_hud.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_runtime_navigation_hud_guard.py

.PHONY: verify.frontend.home_suggestion_semantics.guard
verify.frontend.home_suggestion_semantics.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_home_suggestion_semantics_guard.py

.PHONY: verify.frontend.home_layout_section_coverage.guard
verify.frontend.home_layout_section_coverage.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_home_layout_section_coverage_guard.py

.PHONY: verify.frontend.home_orchestration_consumption.guard
verify.frontend.home_orchestration_consumption.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_home_orchestration_consumption_guard.py

.PHONY: verify.scene.ready.strict_contract.guard
verify.scene.ready.strict_contract.guard: guard.prod.forbid
	@python3 scripts/verify/scene_ready_strict_contract_guard.py

.PHONY: verify.scene.ready.strict_gap.full_audit
verify.scene.ready.strict_gap.full_audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/scene_ready_strict_gap_full_audit.py

.PHONY: verify.workspace_home.sections_schema.guard
verify.workspace_home.sections_schema.guard: guard.prod.forbid
	@python3 scripts/verify/workspace_home_sections_schema_guard.py

.PHONY: verify.workspace_home.orchestration_schema.guard
verify.workspace_home.orchestration_schema.guard: guard.prod.forbid
	@python3 scripts/verify/workspace_home_orchestration_schema_guard.py

.PHONY: verify.workspace_home.provider_split.guard
verify.workspace_home.provider_split.guard: guard.prod.forbid
	@python3 scripts/verify/workspace_home_provider_split_guard.py

.PHONY: verify.workbench.product_acceptance.guard
verify.workbench.product_acceptance.guard: guard.prod.forbid
	@python3 scripts/verify/workbench_product_acceptance_guard.py

.PHONY: verify.frontend.contract_text_hardcode.guard
verify.frontend.contract_text_hardcode.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_contract_text_hardcode_guard.py

.PHONY: verify.frontend.page_contract_boundary.guard
verify.frontend.page_contract_boundary.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_page_contract_boundary_guard.py

.PHONY: verify.frontend.page_contract.sections_coverage.guard
verify.frontend.page_contract.sections_coverage.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_page_contract_sections_coverage_guard.py

.PHONY: verify.frontend.page_contract.key_consistency.guard
verify.frontend.page_contract.key_consistency.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_page_contract_key_consistency_guard.py

.PHONY: verify.frontend.page_contract.section_tag_coverage.guard
verify.frontend.page_contract.section_tag_coverage.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_page_contract_section_tag_coverage_guard.py

.PHONY: verify.frontend.page_contract.section_style_coverage.guard
verify.frontend.page_contract.section_style_coverage.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_page_contract_section_style_coverage_guard.py

.PHONY: verify.frontend.page_contract.orchestration_consumption.guard
verify.frontend.page_contract.orchestration_consumption.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_page_contract_orchestration_consumption_guard.py

.PHONY: verify.frontend.page_contract.runtime_universal.guard
verify.frontend.page_contract.runtime_universal.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_page_contract_runtime_universal_guard.py

.PHONY: verify.frontend.page_block_renderer_smoke
verify.frontend.page_block_renderer_smoke: guard.prod.forbid
	@python3 scripts/verify/frontend_page_block_renderer_smoke_guard.py

.PHONY: verify.frontend.page_block_visual_snapshot_guard
verify.frontend.page_block_visual_snapshot_guard: guard.prod.forbid
	@python3 scripts/verify/frontend_page_block_visual_snapshot_guard.py

.PHONY: verify.frontend.portal_dashboard_block_migration
verify.frontend.portal_dashboard_block_migration: guard.prod.forbid
	@python3 scripts/verify/frontend_portal_dashboard_block_migration_guard.py

.PHONY: verify.frontend.workbench_block_migration
verify.frontend.workbench_block_migration: guard.prod.forbid
	@python3 scripts/verify/frontend_workbench_block_migration_guard.py

.PHONY: verify.frontend.my_work_block_migration
verify.frontend.my_work_block_migration: guard.prod.forbid
	@python3 scripts/verify/frontend_my_work_block_migration_guard.py

.PHONY: verify.frontend.page_block_registry_guard
verify.frontend.page_block_registry_guard: guard.prod.forbid
	@python3 scripts/verify/frontend_page_block_registry_guard.py

.PHONY: verify.frontend.page_legacy_renderer_residue_guard
verify.frontend.page_legacy_renderer_residue_guard: guard.prod.forbid
	@python3 scripts/verify/frontend_page_legacy_renderer_residue_guard.py

.PHONY: verify.frontend.page_renderer_default_guard
verify.frontend.page_renderer_default_guard: guard.prod.forbid
	@python3 scripts/verify/frontend_page_renderer_default_guard.py

.PHONY: verify.page_orchestration.target_completion.guard
verify.page_orchestration.target_completion.guard: guard.prod.forbid
	@python3 scripts/verify/page_orchestration_target_completion_guard.py

.PHONY: verify.page_contract.sections_schema.guard
verify.page_contract.sections_schema.guard: guard.prod.forbid
	@python3 scripts/verify/page_contract_sections_schema_guard.py

.PHONY: verify.page_contract.orchestration_schema.guard
verify.page_contract.orchestration_schema.guard: guard.prod.forbid
	@python3 scripts/verify/page_contract_orchestration_schema_guard.py

.PHONY: verify.page_contract.role_orchestration_variance.guard
verify.page_contract.role_orchestration_variance.guard: guard.prod.forbid
	@python3 scripts/verify/page_contract_role_orchestration_variance_guard.py

.PHONY: verify.page_contract.action_schema_semantics.guard
verify.page_contract.action_schema_semantics.guard: guard.prod.forbid
	@python3 scripts/verify/page_contract_action_schema_semantics_guard.py

.PHONY: verify.page_contract.data_source_semantics.guard
verify.page_contract.data_source_semantics.guard: guard.prod.forbid
	@python3 scripts/verify/page_contract_data_source_semantics_guard.py

.PHONY: verify.orchestration.semantics_registry.guard
verify.orchestration.semantics_registry.guard: guard.prod.forbid
	@python3 scripts/verify/orchestration_semantics_registry_guard.py

.PHONY: verify.page_contract.text_key_coverage.guard
verify.page_contract.text_key_coverage.guard: guard.prod.forbid
	@python3 scripts/verify/page_contract_text_key_coverage_guard.py

.PHONY: verify.page_contract.provider_split.guard
verify.page_contract.provider_split.guard: guard.prod.forbid
	@python3 scripts/verify/page_contract_provider_split_guard.py

.PHONY: verify.page_contract.semantic_provider_split.guard
verify.page_contract.semantic_provider_split.guard: guard.prod.forbid
	@python3 scripts/verify/page_contract_semantic_provider_split_guard.py

.PHONY: verify.page_contract.strategy_provider_split.guard
verify.page_contract.strategy_provider_split.guard: guard.prod.forbid
	@python3 scripts/verify/page_contract_strategy_provider_split_guard.py

.PHONY: verify.page_contract.role_strategy_provider_split.guard
verify.page_contract.role_strategy_provider_split.guard: guard.prod.forbid
	@python3 scripts/verify/page_contract_role_strategy_provider_split_guard.py

.PHONY: verify.list.surface.clean
verify.list.surface.clean: guard.prod.forbid
	@python3 scripts/verify/list_surface_clean_guard.py

.PHONY: verify.frontend.scene_record_semantics.guard
verify.frontend.scene_record_semantics.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_scene_record_semantics_guard.py

.PHONY: verify.frontend.scene_contract_auto_render.guard
verify.frontend.scene_contract_auto_render.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_scene_contract_auto_render_guard.py

.PHONY: verify.frontend.actionview.scene_specialcase.guard
verify.frontend.actionview.scene_specialcase.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_actionview_scene_specialcase_guard.py

.PHONY: verify.frontend.error_context.contract.guard
verify.frontend.error_context.contract.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_error_context_contract_guard.py

.PHONY: verify.frontend.contract_consumer_intrusion.report
verify.frontend.contract_consumer_intrusion.report: guard.prod.forbid
	@python3 scripts/verify/frontend_contract_consumer_intrusion_guard.py --report-only

.PHONY: verify.frontend.contract_consumer_intrusion.guard
verify.frontend.contract_consumer_intrusion.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_contract_consumer_intrusion_guard.py

.PHONY: verify.frontend.list_selection_contract_smoke
verify.frontend.list_selection_contract_smoke: guard.prod.forbid
	@cd frontend/apps/web && pnpm exec node scripts/list_selection_contract_smoke.mjs

.PHONY: verify.render.semantic.ready
verify.render.semantic.ready: guard.prod.forbid
	@python3 scripts/verify/render_semantic_ready_guard.py

.PHONY: verify.contract.governance.determinism.guard
verify.contract.governance.determinism.guard: guard.prod.forbid
	@python3 scripts/verify/contract_governance_determinism_guard.py

.PHONY: verify.render.policy.ready
verify.render.policy.ready: guard.prod.forbid verify.contract.governance.determinism.guard
	@python3 scripts/verify/render_policy_ready_guard.py

.PHONY: verify.frontend.product.ready
verify.frontend.product.ready: guard.prod.forbid \
	verify.scene.ready.strict_contract.guard \
	verify.frontend.contract_runtime.guard \
	verify.frontend.contract_route.guard \
	verify.frontend.contract_normalized_fields.guard \
	verify.frontend.contract_query_context.guard \
	verify.frontend.contract_record_layout.guard \
	verify.frontend.product.contract_consumption.guard \
	verify.frontend.runtime_navigation_hud.guard \
	verify.frontend.home_suggestion_semantics.guard \
	verify.frontend.home_layout_section_coverage.guard \
	verify.frontend.home_orchestration_consumption.guard \
	verify.workspace_home.sections_schema.guard \
	verify.workspace_home.orchestration_schema.guard \
	verify.workspace_home.provider_split.guard \
	verify.frontend.contract_text_hardcode.guard \
	verify.frontend.page_contract_boundary.guard \
	verify.frontend.page_contract.sections_coverage.guard \
	verify.frontend.page_contract.key_consistency.guard \
	verify.frontend.page_contract.section_tag_coverage.guard \
	verify.frontend.page_contract.section_style_coverage.guard \
	verify.frontend.page_contract.orchestration_consumption.guard \
	verify.frontend.page_contract.runtime_universal.guard \
	verify.frontend.page_block_renderer_smoke \
	verify.frontend.page_block_visual_snapshot_guard \
	verify.frontend.portal_dashboard_block_migration \
	verify.frontend.workbench_block_migration \
	verify.frontend.my_work_block_migration \
	verify.frontend.page_block_registry_guard \
	verify.frontend.page_legacy_renderer_residue_guard \
	verify.frontend.page_renderer_default_guard \
	verify.page_orchestration.target_completion.guard \
	verify.page_contract.sections_schema.guard \
	verify.page_contract.orchestration_schema.guard \
	verify.page_contract.role_orchestration_variance.guard \
	verify.page_contract.action_schema_semantics.guard \
	verify.page_contract.data_source_semantics.guard \
	verify.orchestration.semantics_registry.guard \
	verify.page_contract.text_key_coverage.guard \
	verify.page_contract.provider_split.guard \
	verify.page_contract.semantic_provider_split.guard \
	verify.page_contract.strategy_provider_split.guard \
	verify.page_contract.role_strategy_provider_split.guard \
	verify.list.surface.clean \
	verify.frontend.scene_contract_auto_render.guard \
	verify.frontend.actionview.scene_specialcase.guard \
	verify.frontend.scene_record_semantics.guard \
	verify.frontend.error_context.contract.guard \
	verify.render.semantic.ready \
	verify.render.policy.ready \
	verify.frontend_api \
	verify.ui.product.stability
	@echo "[OK] verify.frontend.product.ready done"

.PHONY: verify.product.fullstack.ready
verify.product.fullstack.ready: guard.prod.forbid verify.product.release.ready verify.usage.product.clean verify.frontend.product.ready
	@echo "[OK] verify.product.fullstack.ready done"

verify.scene.legacy_endpoint.guard: guard.prod.forbid
	@python3 scripts/verify/legacy_scene_endpoint_guard.py

verify.scene.legacy_contract.guard: guard.prod.forbid
	@python3 scripts/verify/scene_legacy_contract_guard.py

verify.scene.legacy.contract.guard: verify.scene.legacy_contract.guard
	@echo "[OK] verify.scene.legacy.contract.guard alias -> verify.scene.legacy_contract.guard"

verify.scene.legacy_docs.guard: guard.prod.forbid
	@python3 scripts/verify/scene_legacy_docs_guard.py

verify.scene.legacy_auth.smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/scene_legacy_auth_smoke.py

verify.scene.legacy_deprecation.smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/scene_legacy_deprecation_smoke.py

verify.scene.legacy.bundle: guard.prod.forbid verify.scene.legacy_contract.guard verify.scene.legacy_docs.guard verify.scene.legacy_auth.smoke verify.scene.legacy_deprecation.smoke
	@echo "[OK] verify.scene.legacy.bundle done"

verify.scene.legacy.all: guard.prod.forbid verify.scene.legacy_endpoint.guard verify.scene.legacy.bundle
	@echo "[OK] verify.scene.legacy.all done"

verify.intent.router.purity: guard.prod.forbid
	@python3 scripts/verify/intent_router_purity_guard.py

verify.scene.definition.semantics: guard.prod.forbid
	@python3 scripts/verify/scene_definition_semantics_guard.py

verify.scene.catalog.source.guard: guard.prod.forbid
	@python3 scripts/verify/scene_catalog_source_guard.py

verify.model.ui_dependency.guard: guard.prod.forbid
	@python3 scripts/verify/model_ui_dependency_guard.py

verify.business.shape.guard: guard.prod.forbid
	@python3 scripts/verify/business_shape_assembly_guard.py

verify.controller.delegate.guard: guard.prod.forbid
	@python3 scripts/verify/controller_delegate_guard.py

verify.controller.allowlist.routes.guard: guard.prod.forbid
	@python3 scripts/verify/controller_allowlist_routes_guard.py

verify.controller.route.policy.guard: guard.prod.forbid
	@python3 scripts/verify/controller_route_policy_guard.py

verify.controller.boundary.report: guard.prod.forbid
	@python3 scripts/verify/controller_boundary_report.py

verify.controller.boundary.baseline.guard: guard.prod.forbid
	@python3 scripts/verify/controller_boundary_baseline_guard.py

verify.controller.boundary.guard: guard.prod.forbid verify.controller.delegate.guard verify.controller.allowlist.routes.guard verify.controller.route.policy.guard verify.controller.boundary.report verify.controller.boundary.baseline.guard
	@echo "[OK] verify.controller.boundary.guard done"

verify.scene.catalog.runtime_alignment.guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/scene_catalog_runtime_alignment_guard.py

verify.scene.catalog.governance.guard: guard.prod.forbid verify.scene.catalog.source.guard verify.scene.catalog.runtime_alignment.guard
	@echo "[OK] verify.scene.catalog.governance.guard done"

verify.load_view.access.contract.guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/load_view_access_contract_guard.py

verify.business.core_journey.guard: guard.prod.forbid
	@python3 scripts/verify/business_core_journey_guard.py

verify.role.capability_floor.guard: guard.prod.forbid
	@python3 scripts/verify/role_capability_floor_guard.py

verify.role.capability_floor.prod_like: guard.prod.forbid
	@ENV_NAME="$${ENV:-}"; \
	if [ "$${VERIFY_CACHE:-1}" != "0" ] && [ "$$ENV_NAME" != "prod" ] && [ -s artifacts/backend/role_capability_floor_prod_like.json ]; then \
	  echo "[cache] reuse artifacts/backend/role_capability_floor_prod_like.json"; \
	else \
	  python3 scripts/verify/role_capability_floor_prod_like.py; \
	fi

verify.role.capability_floor.prod_like.schema.guard: guard.prod.forbid verify.role.capability_floor.prod_like
	@python3 scripts/verify/role_capability_floor_prod_like_schema_guard.py

verify.role.management_viewer.readonly.guard: guard.prod.forbid verify.role.capability_floor.prod_like
	@python3 scripts/verify/management_viewer_readonly_guard.py

verify.role.project_member.unification.guard: guard.prod.forbid verify.role.capability_floor.prod_like
	@python3 scripts/verify/project_member_unification_guard.py

verify.role.system_admin.minimum_permission_audit.guard: guard.prod.forbid verify.role.capability_floor.prod_like verify.write_intent.permission.audit
	@python3 scripts/verify/system_admin_minimum_permission_audit_guard.py

verify.role.acl.minimum_set.guard: guard.prod.forbid
	@python3 scripts/verify/role_acl_minimum_set_guard.py

verify.project.dashboard.role_runtime.guard: guard.prod.forbid
	@python3 scripts/verify/project_dashboard_role_runtime_guard.py

verify.scene.permission_reasoncode_deeplink.guard: guard.prod.forbid verify.release.capability.audit.schema.guard verify.scene.contract.shape verify.project.dashboard.snapshot
	@python3 scripts/verify/scene_permission_reasoncode_deeplink_guard.py

verify.contract.assembler.semantic.smoke: guard.prod.forbid verify.role.capability_floor.prod_like
	@python3 scripts/verify/contract_assembler_semantic_smoke.py

verify.contract.assembler.semantic.strict: guard.prod.forbid verify.role.capability_floor.prod_like
	@SC_P4_SEMANTIC_STRICT=1 python3 scripts/verify/contract_assembler_semantic_smoke.py

verify.contract.assembler.semantic.schema.guard: guard.prod.forbid verify.contract.assembler.semantic.smoke
	@python3 scripts/verify/contract_assembler_semantic_schema_guard.py

verify.project.form.contract.surface.guard: guard.prod.forbid verify.role.capability_floor.prod_like
	@ENV_NAME="$${ENV:-}"; \
	if [ "$${VERIFY_CACHE:-1}" != "0" ] && [ "$$ENV_NAME" != "prod" ] && [ -s artifacts/backend/project_form_contract_surface_guard.json ]; then \
	  echo "[cache] reuse artifacts/backend/project_form_contract_surface_guard.json"; \
	else \
	  python3 scripts/verify/project_form_contract_surface_guard.py; \
	fi

.PHONY: verify.relation.access_policy.consistency.audit
verify.relation.access_policy.consistency.audit: guard.prod.forbid verify.role.capability_floor.prod_like
	@ENV_NAME="$${ENV:-}"; \
	if [ "$${VERIFY_CACHE:-1}" != "0" ] && [ "$$ENV_NAME" != "prod" ] && [ -s artifacts/backend/relation_access_policy_consistency_audit.json ]; then \
	  echo "[cache] reuse artifacts/backend/relation_access_policy_consistency_audit.json"; \
	else \
	  python3 scripts/verify/relation_access_policy_consistency_audit.py; \
	fi

.PHONY: verify.native_surface_integrity_guard verify.governed_surface_policy_guard verify.contract.native_integrity_guard verify.contract.governed_policy_guard verify.contract.surface_mapping_guard verify.contract.parse_boundary.guard verify.contract.production_chain.guard
verify.native_surface_integrity_guard: guard.prod.forbid verify.role.capability_floor.prod_like
	@ENV_NAME="$${ENV:-}"; \
	if [ "$${VERIFY_CACHE:-1}" != "0" ] && [ "$$ENV_NAME" != "prod" ] && [ -s backend/native_surface_integrity_guard.json ]; then \
	  echo "[cache] reuse backend/native_surface_integrity_guard.json"; \
	else \
	  python3 scripts/verify/native_surface_integrity_guard.py; \
	fi

verify.governed_surface_policy_guard: guard.prod.forbid verify.role.capability_floor.prod_like
	@ENV_NAME="$${ENV:-}"; \
	if [ "$${VERIFY_CACHE:-1}" != "0" ] && [ "$$ENV_NAME" != "prod" ] && [ -s backend/governed_surface_policy_guard.json ]; then \
	  echo "[cache] reuse backend/governed_surface_policy_guard.json"; \
	else \
	  python3 scripts/verify/governed_surface_policy_guard.py; \
	fi

verify.contract.native_integrity_guard: guard.prod.forbid verify.native_surface_integrity_guard
	@echo "[OK] verify.contract.native_integrity_guard done"

verify.contract.governed_policy_guard: guard.prod.forbid verify.governed_surface_policy_guard
	@echo "[OK] verify.contract.governed_policy_guard done"

verify.contract.surface_mapping_guard: guard.prod.forbid verify.role.capability_floor.prod_like
	@ENV_NAME="$${ENV:-}"; \
	if [ "$${VERIFY_CACHE:-1}" != "0" ] && [ "$$ENV_NAME" != "prod" ] && [ -s artifacts/backend/surface_mapping_guard.json ]; then \
	  echo "[cache] reuse artifacts/backend/surface_mapping_guard.json"; \
	else \
	  python3 scripts/verify/surface_mapping_guard.py; \
	fi

verify.contract.parse_boundary.guard: guard.prod.forbid
	@python3 scripts/verify/contract_parse_boundary_guard.py

verify.contract.production_chain.guard: guard.prod.forbid
	@python3 scripts/verify/contract_production_chain_guard.py

verify.runtime.surface.dashboard.report: guard.prod.forbid verify.scene.catalog.runtime_alignment.guard verify.role.capability_floor.prod_like
	@python3 scripts/verify/runtime_surface_dashboard_report.py

verify.runtime.surface.dashboard.schema.guard: guard.prod.forbid verify.runtime.surface.dashboard.report
	@python3 scripts/verify/runtime_surface_dashboard_schema_guard.py

verify.runtime.surface.dashboard.strict.guard: guard.prod.forbid verify.runtime.surface.dashboard.report verify.runtime.surface.dashboard.schema.guard
	@python3 scripts/verify/runtime_surface_dashboard_strict_guard.py

verify.backend.architecture.full.report: guard.prod.forbid
	@python3 scripts/verify/backend_architecture_full_report.py

verify.backend.architecture.full.report.schema.guard: guard.prod.forbid verify.backend.architecture.full.report
	@python3 scripts/verify/backend_architecture_full_report_schema_guard.py

verify.backend.architecture.full.report.guard: guard.prod.forbid verify.backend.architecture.full.report.schema.guard
	@python3 scripts/verify/backend_architecture_full_report_guard.py

verify.backend.architecture.full.report.guard.schema.guard: guard.prod.forbid verify.backend.architecture.full.report.guard
	@python3 scripts/verify/backend_architecture_full_report_guard_schema_guard.py

verify.backend.evidence.manifest: guard.prod.forbid verify.contract.evidence.guard verify.backend.architecture.full.report.guard
	@python3 scripts/verify/backend_evidence_manifest.py

verify.backend.evidence.manifest.schema.guard: guard.prod.forbid verify.backend.evidence.manifest
	@python3 scripts/verify/backend_evidence_manifest_schema_guard.py

verify.backend.evidence.manifest.guard: guard.prod.forbid verify.backend.evidence.manifest.schema.guard
	@python3 scripts/verify/backend_evidence_manifest_guard.py

verify.capability.core.health.report: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/capability_core_health_report.py

verify.capability.core.health.schema.guard: guard.prod.forbid verify.capability.core.health.report
	@python3 scripts/verify/capability_core_health_report_schema_guard.py

verify.scene.contract.semantic.v2.guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/scene_contract_semantic_v2_guard.py

verify.phase_next.evidence.bundle: guard.prod.forbid verify.role.capability_floor.prod_like verify.role.capability_floor.prod_like.schema.guard verify.load_view.access.contract.guard verify.contract.assembler.semantic.smoke verify.contract.assembler.semantic.schema.guard verify.project.form.contract.surface.guard verify.runtime.surface.dashboard.report verify.runtime.surface.dashboard.schema.guard verify.scene.capability.matrix.schema.guard verify.capability.core.health.schema.guard verify.scene.contract.semantic.v2.guard verify.native_view.semantic_page verify.unified_page_contract.v2
	@echo "[OK] verify.phase_next.evidence.bundle done"

verify.phase_next.evidence.bundle.strict: guard.prod.forbid verify.phase_next.evidence.bundle verify.contract.assembler.semantic.strict verify.runtime.surface.dashboard.strict.guard verify.backend.architecture.full.report.guard
	@$(MAKE) --no-print-directory verify.backend.evidence.manifest.guard
	@echo "[OK] verify.phase_next.evidence.bundle.strict done"

verify.business.capability_baseline.report: guard.prod.forbid
	@python3 scripts/verify/business_capability_baseline_report.py

verify.business.capability_baseline.report.schema.guard: guard.prod.forbid verify.business.capability_baseline.report
	@python3 scripts/verify/business_capability_baseline_report_schema_guard.py

verify.business.capability_baseline.report.guard: guard.prod.forbid verify.business.capability_baseline.report.schema.guard
	@python3 scripts/verify/business_capability_baseline_report_guard.py

verify.business.capability_baseline.guard: guard.prod.forbid verify.scene.catalog.runtime_alignment.guard verify.business.core_journey.guard verify.role.capability_floor.guard verify.business.capability_baseline.report.guard
	@echo "[OK] verify.business.capability_baseline.guard done"

.PHONY: verify.system.capability_baseline.report
verify.system.capability_baseline.report: guard.prod.forbid
	@python3 scripts/verify/system_capability_baseline_report.py
	@python3 scripts/verify/system_capability_baseline_report_schema_guard.py

.PHONY: verify.system.capability_baseline.report.schema.guard
verify.system.capability_baseline.report.schema.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/system_capability_baseline_report_schema_guard.py
	@python3 scripts/verify/system_capability_baseline_report_schema_guard.py

verify.contract.evidence.export: guard.prod.forbid audit.intent.surface verify.scene.contract.shape verify.business.capability_baseline.guard verify.contract.scene_coverage.brief verify.backend.architecture.full.report.schema.guard
	@python3 scripts/contract/export_evidence.py

verify.contract.evidence.schema.guard: guard.prod.forbid verify.contract.evidence.export
	@python3 scripts/verify/contract_evidence_schema_guard.py

verify.contract.evidence.guard: guard.prod.forbid verify.contract.evidence.schema.guard
	@python3 scripts/verify/contract_evidence_guard.py

verify.baseline.policy_integrity.guard: guard.prod.forbid
	@python3 scripts/verify/baseline_policy_integrity_guard.py

verify.scene.demo_leak.guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/scene_demo_leak_guard.py

verify.contract.ordering.smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/scene_order_determinism_smoke.py

verify.contract.catalog.determinism: guard.prod.forbid
	@python3 scripts/verify/contract_catalog_determinism_guard.py

verify.contract.envelope.guard: guard.prod.forbid
	@python3 scripts/verify/contract_envelope_guard.py

verify.contract.envelope: guard.prod.forbid verify.contract.envelope.guard verify.contract.mode.smoke verify.contract.api.mode.smoke verify.scene_capability.contract.guard
	@echo "[OK] verify.contract.envelope done"

verify.scene.runtime_boundary.gate: guard.prod.forbid verify.boundary.import_guard verify.backend.boundary_guard verify.model.ui_dependency.guard verify.business.shape.guard verify.controller.boundary.guard verify.frontend.intent_channel.guard verify.frontend.no_base_contract_direct_consume.guard verify.frontend.scene_governance_consumption.guard verify.scene.provider.guard verify.scene.provider_shape.guard verify.scene.contract_v1.field_schema.guard verify.scene.engine_migration.matrix.guard verify.scene.legacy_endpoint.guard verify.intent.router.purity verify.scene.input_boundary.guard verify.scene.governance_payload.guard verify.scene.asset_queue_trend.guard verify.scene.ready.consumption_trend.guard verify.scene.governance_history_report.guard verify.scene.governance_history_archive.guard verify.scene.registry_asset_snapshot.guard verify.scene.base_contract_source_mix.guard verify.scene.source_fallback_burndown.guard verify.scene.no_action_scene.guard verify.scene.sample_registry_diff.guard verify.scene.sample_registry_diff_trend.guard verify.scene.base_contract_asset_coverage.guard verify.scene.orchestrator.input.schema.guard verify.scene.orchestrator.output.schema.guard verify.scene.orchestrator.base_fact_binding.guard verify.scene.orchestrator.industry_interface.guard verify.scene.orchestrator.merge_priority.guard verify.scene.orchestrator.scene_type_surface.guard verify.scene.orchestrator.action_surface.guard verify.scene.orchestrator.key_scene_compile.guard verify.scene.action_surface_strategy.wiring.guard verify.scene.action_surface_strategy.schema.guard verify.scene.action_surface_strategy.payload.guard verify.scene.action_surface_strategy.priority.guard verify.scene.action_surface_strategy.live_matrix.guard verify.scene.ready.scene_type_consumption_metrics.guard verify.scene.validation_recovery_strategy.guard verify.scene.validation_recovery_strategy.payload_path.guard verify.scene.validation_recovery_strategy.e2e_smoke.guard verify.scene.ui_base_contract_canonicalizer.guard verify.scene.ready.strict_contract.guard
	@echo "[OK] verify.scene.runtime_boundary.gate done"

.PHONY: verify.scene.product_delivery.readiness.guard
verify.scene.product_delivery.readiness.guard: guard.prod.forbid
	@python3 scripts/verify/scene_product_delivery_readiness_guard.py

.PHONY: verify.scene.delivery.readiness
verify.scene.delivery.readiness: guard.prod.forbid
	@SC_SCENE_REGISTRY_ASSET_SNAPSHOT_REQUIRE_LIVE=$${SC_SCENE_REGISTRY_ASSET_SNAPSHOT_REQUIRE_LIVE:-1} \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_ALLOW_STATE_FALLBACK_ON_LIVE_FAIL=$${SC_SCENE_REGISTRY_ASSET_SNAPSHOT_ALLOW_STATE_FALLBACK_ON_LIVE_FAIL:-1} \
	SC_SCENE_SAMPLE_REGISTRY_DIFF_REQUIRE_SCENES=$${SC_SCENE_SAMPLE_REGISTRY_DIFF_REQUIRE_SCENES:-1} \
	SC_SCENE_ACTION_STRATEGY_LIVE_MATRIX_REQUIRE_LIVE=$${SC_SCENE_ACTION_STRATEGY_LIVE_MATRIX_REQUIRE_LIVE:-1} \
	SC_SCENE_ACTION_SURFACE_STRATEGY_PAYLOAD_REQUIRE_LIVE=$${SC_SCENE_ACTION_SURFACE_STRATEGY_PAYLOAD_REQUIRE_LIVE:-1} \
	SC_SCENE_READY_CONSUMPTION_TREND_REQUIRE_LIVE=$${SC_SCENE_READY_CONSUMPTION_TREND_REQUIRE_LIVE:-1} \
	SC_SCENE_CONTRACT_V1_FIELD_SCHEMA_ALLOW_STATE_FALLBACK_ON_LIVE_FAIL=$${SC_SCENE_CONTRACT_V1_FIELD_SCHEMA_ALLOW_STATE_FALLBACK_ON_LIVE_FAIL:-1} \
	SC_SCENE_READY_STRICT_GAP_ALLOW_STATE_FALLBACK_ON_LIVE_FAIL=$${SC_SCENE_READY_STRICT_GAP_ALLOW_STATE_FALLBACK_ON_LIVE_FAIL:-1} \
	SC_SCENE_READY_CONSUMPTION_TREND_REQUIRE_ENABLED=$${SC_SCENE_READY_CONSUMPTION_TREND_REQUIRE_ENABLED:-1} \
	$(MAKE) --no-print-directory verify.scene.runtime_boundary.gate
	@SC_SCENE_READY_STRICT_GAP_ALLOW_STATE_FALLBACK_ON_LIVE_FAIL=$${SC_SCENE_READY_STRICT_GAP_ALLOW_STATE_FALLBACK_ON_LIVE_FAIL:-1} \
	SC_SCENE_READY_STRICT_GAP_FULL_AUDIT_STATE_FILE=$${SC_SCENE_READY_STRICT_GAP_FULL_AUDIT_STATE_FILE:-artifacts/backend/scene_contract_v1_field_schema_state.json} \
	$(MAKE) --no-print-directory verify.scene.ready.strict_gap.full_audit
	@$(MAKE) --no-print-directory verify.scene.product_delivery.readiness.guard
	@echo "[INFO] strict guard report: docs/ops/audits/scene_ready_strict_contract_guard_report.md"
	@echo "[INFO] strict full audit report: docs/ops/audits/scene_ready_strict_gap_full_audit.md"
	@echo "[OK] verify.scene.delivery.readiness done"

.PHONY: verify.scene.delivery.readiness.role_matrix
verify.scene.delivery.readiness.role_matrix: guard.prod.forbid
	@$(MAKE) --no-print-directory verify.scene.base_contract_source_mix.role_matrix.guard
	@set +e; python3 scripts/verify/scene_delivery_runtime_gate_decision.py; status=$$?; set -e; \
	if [ "$$status" = "0" ]; then \
	  $(MAKE) --no-print-directory verify.scene.delivery.readiness; \
	elif [ "$$status" = "10" ]; then \
	  true; \
	else \
	  exit "$$status"; \
	fi
	@echo "[OK] verify.scene.delivery.readiness.role_matrix done"

.PHONY: verify.scene.delivery.readiness.role_company_matrix
verify.scene.delivery.readiness.role_company_matrix: guard.prod.forbid
	@$(MAKE) --no-print-directory verify.scene.delivery.readiness.role_matrix
	@$(MAKE) --no-print-directory verify.delivery.journey.role_matrix.guard
	@$(MAKE) --no-print-directory verify.scene.company_snapshot.collect
	@$(MAKE) --no-print-directory verify.scene.company_access.preflight.guard
	@$(MAKE) --no-print-directory verify.scene.base_contract_source_mix.company_matrix.guard
	@$(MAKE) --no-print-directory verify.scene.multi_company.evidence.guard
	@echo "[OK] verify.scene.delivery.readiness.role_company_matrix done"

.PHONY: verify.delivery.journey.role_matrix.guard
verify.delivery.journey.role_matrix.guard: guard.prod.forbid
	@python3 scripts/verify/delivery_journey_role_matrix_guard.py

.PHONY: verify.scene.engine_migration.matrix.guard
verify.scene.engine_migration.matrix.guard: guard.prod.forbid verify.product.delivery.v1.map
	@python3 scripts/verify/scene_engine_migration_matrix_guard.py

.PHONY: verify.scene.source_fallback_burndown.guard
verify.scene.source_fallback_burndown.guard: guard.prod.forbid
	@python3 scripts/verify/scene_source_fallback_burndown_guard.py

.PHONY: verify.scene.multi_company.evidence.guard
verify.scene.multi_company.evidence.guard: guard.prod.forbid
	@python3 scripts/verify/scene_multi_company_evidence_guard.py

.PHONY: verify.scene.company_snapshot.collect
verify.scene.company_snapshot.collect: guard.prod.forbid
	@python3 scripts/verify/scene_company_snapshot_collect.py

.PHONY: verify.scene.company_access.preflight.guard
verify.scene.company_access.preflight.guard: guard.prod.forbid
	@python3 scripts/verify/scene_company_access_preflight_guard.py

.PHONY: ops.scene.company_secondary.access
ops.scene.company_secondary.access: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc " \
	E2E_BASE_URL=http://localhost:8069 \
	DB_NAME=$(DB_NAME) \
	ADMIN_LOGIN=$${ADMIN_LOGIN:-admin} \
	ADMIN_PASSWD=$${ADMIN_PASSWD:-admin} \
	TARGET_LOGIN=$${TARGET_LOGIN:-$${ROLE_PM_LOGIN:-demo_role_pm}} \
	TARGET_COMPANY_ID=$${TARGET_COMPANY_ID:-2} \
	APPLY=$${APPLY:-0} \
	python3 /mnt/scripts/ops/ensure_company_secondary_access.py \
	"

.PHONY: ops.scene.company_secondary.seed
ops.scene.company_secondary.seed: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc " \
	E2E_BASE_URL=http://localhost:8069 \
	DB_NAME=$(DB_NAME) \
	ADMIN_LOGIN=$${ADMIN_LOGIN:-admin} \
	ADMIN_PASSWD=$${ADMIN_PASSWD:-admin} \
	TARGET_LOGIN=$${TARGET_LOGIN:-$${ROLE_PM_LOGIN:-demo_role_pm}} \
	TARGET_USER_NAME='$${TARGET_USER_NAME:-Demo PM Company2}' \
	TARGET_USER_PASSWORD=$${TARGET_USER_PASSWORD:-demo} \
	TARGET_COMPANY_ID=$${TARGET_COMPANY_ID:-2} \
	TARGET_COMPANY_NAME='$${TARGET_COMPANY_NAME:-Demo Secondary Company}' \
	CREATE_COMPANY_IF_MISSING=$${CREATE_COMPANY_IF_MISSING:-1} \
	CREATE_USER_IF_MISSING=$${CREATE_USER_IF_MISSING:-0} \
	SET_PRIMARY_COMPANY=$${SET_PRIMARY_COMPANY:-0} \
	APPLY=$${APPLY:-0} \
	python3 /mnt/scripts/ops/seed_company_secondary_access.py \
	"

.PHONY: verify.scene.input_boundary.guard
verify.scene.input_boundary.guard: guard.prod.forbid
	@python3 scripts/verify/scene_input_boundary_guard.py

.PHONY: verify.scene.governance_payload.guard
verify.scene.governance_payload.guard: guard.prod.forbid
	@python3 scripts/verify/scene_governance_payload_guard.py

.PHONY: verify.scene.asset_queue_trend.guard
verify.scene.asset_queue_trend.guard: guard.prod.forbid
	@python3 scripts/verify/scene_asset_queue_trend_guard.py

.PHONY: verify.scene.orchestrator.input.schema.guard
verify.scene.orchestrator.input.schema.guard: guard.prod.forbid
	@python3 scripts/verify/scene_orchestrator_input_schema_guard.py

.PHONY: verify.scene.orchestrator.output.schema.guard
verify.scene.orchestrator.output.schema.guard: guard.prod.forbid
	@python3 scripts/verify/scene_orchestrator_output_schema_guard.py

.PHONY: verify.scene.orchestrator.base_fact_binding.guard
verify.scene.orchestrator.base_fact_binding.guard: guard.prod.forbid
	@python3 scripts/verify/scene_orchestrator_base_fact_binding_guard.py

.PHONY: verify.scene.orchestrator.industry_interface.guard
verify.scene.orchestrator.industry_interface.guard: guard.prod.forbid
	@python3 scripts/verify/scene_orchestrator_industry_interface_guard.py

.PHONY: verify.scene.orchestrator.merge_priority.guard
verify.scene.orchestrator.merge_priority.guard: guard.prod.forbid
	@python3 scripts/verify/scene_orchestrator_merge_priority_guard.py

.PHONY: verify.scene.orchestrator.scene_type_surface.guard
verify.scene.orchestrator.scene_type_surface.guard: guard.prod.forbid
	@python3 scripts/verify/scene_orchestrator_scene_type_surface_guard.py

.PHONY: verify.scene.orchestrator.action_surface.guard
verify.scene.orchestrator.action_surface.guard: guard.prod.forbid
	@python3 scripts/verify/scene_orchestrator_action_surface_guard.py

.PHONY: verify.scene.orchestrator.key_scene_compile.guard
verify.scene.orchestrator.key_scene_compile.guard: guard.prod.forbid
	@python3 scripts/verify/scene_orchestrator_key_scene_compile_guard.py

.PHONY: verify.scene.action_surface_strategy.wiring.guard
verify.scene.action_surface_strategy.wiring.guard: guard.prod.forbid
	@python3 scripts/verify/scene_action_surface_strategy_wiring_guard.py

.PHONY: verify.scene.action_surface_strategy.schema.guard
verify.scene.action_surface_strategy.schema.guard: guard.prod.forbid
	@python3 scripts/verify/scene_action_surface_strategy_schema_guard.py

.PHONY: verify.scene.action_surface_strategy.payload.guard
verify.scene.action_surface_strategy.payload.guard: guard.prod.forbid
	@python3 scripts/verify/scene_action_surface_strategy_payload_guard.py

.PHONY: verify.scene.action_surface_strategy.priority.guard
verify.scene.action_surface_strategy.priority.guard: guard.prod.forbid
	@python3 scripts/verify/scene_action_surface_strategy_priority_guard.py

.PHONY: verify.scene.action_surface_strategy.live_matrix.guard
verify.scene.action_surface_strategy.live_matrix.guard: guard.prod.forbid
	@python3 scripts/verify/scene_action_surface_strategy_live_matrix_guard.py

.PHONY: verify.scene.ready.scene_type_consumption_metrics.guard
verify.scene.ready.scene_type_consumption_metrics.guard: guard.prod.forbid
	@python3 scripts/verify/scene_ready_scene_type_consumption_metrics_guard.py

.PHONY: verify.scene.ready.consumption_trend.guard
verify.scene.ready.consumption_trend.guard: guard.prod.forbid
	@python3 scripts/verify/scene_ready_consumption_trend_guard.py

.PHONY: verify.scene.ready.blocks_by_view.guard
verify.scene.ready.blocks_by_view.guard: guard.prod.forbid
	@python3 scripts/verify/scene_ready_blocks_by_view_guard.py

.PHONY: verify.scene.governance_history_report.guard
verify.scene.governance_history_report.guard: guard.prod.forbid
	@python3 scripts/verify/scene_governance_history_report_guard.py

.PHONY: verify.scene.governance_history_archive.guard
verify.scene.governance_history_archive.guard: guard.prod.forbid
	@python3 scripts/verify/scene_governance_history_archive_guard.py

.PHONY: verify.scene.registry_asset_snapshot.guard
verify.scene.registry_asset_snapshot.guard: guard.prod.forbid
	@python3 scripts/verify/scene_registry_asset_snapshot_guard.py

.PHONY: verify.scene.base_contract_source_mix.guard
verify.scene.base_contract_source_mix.guard: guard.prod.forbid
	@python3 scripts/verify/scene_base_contract_source_mix_guard.py

.PHONY: verify.scene.no_action_scene.guard
verify.scene.no_action_scene.guard: guard.prod.forbid
	@python3 scripts/verify/scene_no_action_scene_guard.py

.PHONY: verify.scene.registry_asset_snapshot.executive
verify.scene.registry_asset_snapshot.executive: guard.prod.forbid
	@SC_SCENE_REGISTRY_ASSET_SNAPSHOT_REQUIRE_LIVE=1 \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_RETRIES=$${SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_RETRIES:-3} \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_BACKOFF_SEC=$${SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_BACKOFF_SEC:-1} \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_ALLOW_STATE_FALLBACK_ON_LIVE_FAIL=1 \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_STATE_FILE=artifacts/backend/scene_registry_asset_snapshot_state.executive.json \
	E2E_LOGIN=$${ROLE_EXECUTIVE_LOGIN:-demo_role_executive} \
	E2E_PASSWORD=$${ROLE_EXECUTIVE_PASSWORD:-demo} \
	python3 scripts/verify/scene_registry_asset_snapshot_guard.py

.PHONY: verify.scene.registry_asset_snapshot.pm
verify.scene.registry_asset_snapshot.pm: guard.prod.forbid
	@SC_SCENE_REGISTRY_ASSET_SNAPSHOT_REQUIRE_LIVE=1 \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_RETRIES=$${SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_RETRIES:-3} \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_BACKOFF_SEC=$${SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_BACKOFF_SEC:-1} \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_ALLOW_STATE_FALLBACK_ON_LIVE_FAIL=1 \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_STATE_FILE=artifacts/backend/scene_registry_asset_snapshot_state.pm.json \
	E2E_LOGIN=$${ROLE_PM_LOGIN:-demo_role_pm} \
	E2E_PASSWORD=$${ROLE_PM_PASSWORD:-demo} \
	python3 scripts/verify/scene_registry_asset_snapshot_guard.py

.PHONY: verify.scene.registry_asset_snapshot.finance
verify.scene.registry_asset_snapshot.finance: guard.prod.forbid
	@SC_SCENE_REGISTRY_ASSET_SNAPSHOT_REQUIRE_LIVE=1 \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_RETRIES=$${SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_RETRIES:-3} \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_BACKOFF_SEC=$${SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_BACKOFF_SEC:-1} \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_ALLOW_STATE_FALLBACK_ON_LIVE_FAIL=1 \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_STATE_FILE=artifacts/backend/scene_registry_asset_snapshot_state.finance.json \
	E2E_LOGIN=$${ROLE_FINANCE_LOGIN:-demo_role_finance} \
	E2E_PASSWORD=$${ROLE_FINANCE_PASSWORD:-$${ROLE_PM_PASSWORD:-demo}} \
	python3 scripts/verify/scene_registry_asset_snapshot_guard.py

.PHONY: verify.scene.registry_asset_snapshot.ops
verify.scene.registry_asset_snapshot.ops: guard.prod.forbid
	@SC_SCENE_REGISTRY_ASSET_SNAPSHOT_REQUIRE_LIVE=1 \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_RETRIES=$${SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_RETRIES:-3} \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_BACKOFF_SEC=$${SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_BACKOFF_SEC:-1} \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_ALLOW_STATE_FALLBACK_ON_LIVE_FAIL=1 \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_STATE_FILE=artifacts/backend/scene_registry_asset_snapshot_state.ops.json \
	E2E_LOGIN=$${ROLE_OPS_LOGIN:-$${ROLE_EXECUTIVE_LOGIN:-demo_role_executive}} \
	E2E_PASSWORD=$${ROLE_OPS_PASSWORD:-$${ROLE_EXECUTIVE_PASSWORD:-demo}} \
	python3 scripts/verify/scene_registry_asset_snapshot_guard.py

.PHONY: verify.scene.registry_asset_snapshot.company_primary
verify.scene.registry_asset_snapshot.company_primary: guard.prod.forbid
	@SC_SCENE_REGISTRY_ASSET_SNAPSHOT_REQUIRE_LIVE=1 \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_RETRIES=$${SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_RETRIES:-3} \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_BACKOFF_SEC=$${SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_BACKOFF_SEC:-1} \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_ALLOW_STATE_FALLBACK_ON_LIVE_FAIL=1 \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_STATE_FILE=artifacts/backend/scene_registry_asset_snapshot_state.company_primary.json \
	E2E_LOGIN=$${COMPANY_PRIMARY_LOGIN:-admin} \
	E2E_PASSWORD=$${COMPANY_PRIMARY_PASSWORD:-$${ADMIN_PASSWD:-admin}} \
	E2E_COMPANY_ID=$${COMPANY_PRIMARY_ID:-1} \
	python3 scripts/verify/scene_registry_asset_snapshot_guard.py

.PHONY: verify.scene.registry_asset_snapshot.company_secondary
verify.scene.registry_asset_snapshot.company_secondary: guard.prod.forbid
	@SC_SCENE_REGISTRY_ASSET_SNAPSHOT_REQUIRE_LIVE=1 \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_RETRIES=$${SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_RETRIES:-3} \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_BACKOFF_SEC=$${SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_BACKOFF_SEC:-1} \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_ALLOW_STATE_FALLBACK_ON_LIVE_FAIL=1 \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_STATE_FILE=artifacts/backend/scene_registry_asset_snapshot_state.company_secondary.json \
	E2E_LOGIN=$${COMPANY_SECONDARY_LOGIN:-$${ROLE_PM_LOGIN:-demo_role_pm}} \
	E2E_PASSWORD=$${COMPANY_SECONDARY_PASSWORD:-$${ROLE_PM_PASSWORD:-demo}} \
	E2E_COMPANY_ID=$${COMPANY_SECONDARY_ID:-2} \
	python3 scripts/verify/scene_registry_asset_snapshot_guard.py

.PHONY: verify.scene.base_contract_source_mix.role_matrix.guard
verify.scene.base_contract_source_mix.role_matrix.guard: guard.prod.forbid verify.scene.registry_asset_snapshot.executive verify.scene.registry_asset_snapshot.pm verify.scene.registry_asset_snapshot.finance verify.scene.registry_asset_snapshot.ops
	@python3 scripts/verify/scene_base_contract_source_mix_role_matrix_guard.py

.PHONY: verify.scene.base_contract_source_mix.company_matrix.guard
verify.scene.base_contract_source_mix.company_matrix.guard: guard.prod.forbid verify.scene.registry_asset_snapshot.company_primary verify.scene.registry_asset_snapshot.company_secondary
	@python3 scripts/verify/scene_base_contract_source_mix_company_matrix_guard.py

.PHONY: verify.scene.sample_registry_diff.guard
verify.scene.sample_registry_diff.guard: guard.prod.forbid
	@python3 scripts/verify/scene_sample_registry_diff_guard.py

.PHONY: verify.scene.sample_registry_diff_trend.guard
verify.scene.sample_registry_diff_trend.guard: guard.prod.forbid
	@python3 scripts/verify/scene_sample_registry_diff_trend_guard.py

.PHONY: verify.scene.validation_recovery_strategy.guard
verify.scene.validation_recovery_strategy.guard: guard.prod.forbid
	@python3 scripts/verify/scene_validation_recovery_strategy_guard.py

.PHONY: verify.scene.validation_recovery_strategy.payload_path.guard
verify.scene.validation_recovery_strategy.payload_path.guard: guard.prod.forbid
	@python3 scripts/verify/scene_validation_recovery_strategy_payload_path_guard.py

.PHONY: verify.scene.validation_recovery_strategy.e2e_smoke.guard
verify.scene.validation_recovery_strategy.e2e_smoke.guard: guard.prod.forbid
	@python3 scripts/verify/scene_validation_recovery_strategy_e2e_smoke_guard.py

.PHONY: verify.scene.ui_base_contract_canonicalizer.guard
verify.scene.ui_base_contract_canonicalizer.guard: guard.prod.forbid
	@python3 scripts/verify/scene_ui_base_contract_canonicalizer_guard.py

.PHONY: verify.frontend.no_base_contract_direct_consume.guard
verify.frontend.no_base_contract_direct_consume.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_no_base_contract_direct_consume_guard.py

.PHONY: verify.frontend.scene_governance_consumption.guard
verify.frontend.scene_governance_consumption.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_scene_governance_consumption_guard.py

.PHONY: verify.scene.base_contract_asset_coverage.guard
verify.scene.base_contract_asset_coverage.guard: guard.prod.forbid
	@python3 scripts/verify/scene_base_contract_asset_coverage_guard.py

verify.scene.contract_path.gate: guard.prod.forbid verify.scene.runtime_boundary.gate verify.scene.legacy.bundle
	@echo "[OK] verify.scene.contract_path.gate done"

verify.seed.demo.import_boundary.guard: guard.prod.forbid
	@python3 scripts/verify/seed_demo_import_boundary_guard.py

verify.seed.demo.isolation: guard.prod.forbid verify.scene.provider.guard verify.seed.demo.import_boundary.guard verify.test_seed_dependency.guard verify.scene.demo_leak.guard
	@echo "[OK] verify.seed.demo.isolation done"

# Unified aliases for CI/operations wording.
.PHONY: verify.contract.handler_boundary.guard
verify.contract.handler_boundary.guard: guard.prod.forbid
	@python3 scripts/verify/contract_handler_layout_boundary_guard.py

verify.boundary.guard: guard.prod.forbid verify.scene.contract_path.gate verify.contract.handler_boundary.guard
	@echo "[OK] verify.boundary.guard done"

.PHONY: verify.system_init.runtime_context.stability
verify.system_init.snapshot_equivalence: guard.prod.forbid
	@HTTP_SMOKE_TIMEOUT_SECONDS="$${HTTP_SMOKE_TIMEOUT_SECONDS:-180}" $(RUN_ENV) python3 scripts/verify/system_init_snapshot_equivalence.py

verify.system_init.runtime_context.stability: guard.prod.forbid
	@$(RUN_ENV) python3 scripts/verify/system_init_runtime_context_stability.py

verify.intent.capability.matrix.report: guard.prod.forbid
	@python3 scripts/verify/intent_capability_matrix_report.py

verify.intent.layered.catalog: guard.prod.forbid verify.intent.capability.matrix.report
	@python3 scripts/verify/intent_layered_catalog_report.py

.PHONY: verify.intent.write.guard
verify.intent.write.guard: guard.prod.forbid
	@python3 addons/smart_core/tools/intent_write_guard.py

.PHONY: verify.intent.acl.mode
verify.intent.acl.mode: guard.prod.forbid
	@python3 addons/smart_core/tools/intent_acl_mode_guard.py

verify.write_intent.permission.audit: guard.prod.forbid
	@python3 scripts/verify/write_intent_permission_audit.py

verify.scene.intent.matrix.report: guard.prod.forbid
	@python3 scripts/verify/scene_intent_matrix_report.py

verify.scene.intent.consistency: guard.prod.forbid verify.intent.layered.catalog
	@python3 scripts/verify/scene_intent_consistency_guard.py

verify.intent.orphan.report: guard.prod.forbid
	@python3 scripts/verify/intent_orphan_report.py

verify.capability.scene.matrix.report: guard.prod.forbid
	@python3 scripts/verify/capability_scene_matrix_report.py

verify.intent.execution.path.report: guard.prod.forbid verify.intent.permission.matrix.report
	@python3 scripts/verify/intent_execution_path_report.py

verify.platform.kernel.baseline: guard.prod.forbid verify.intent.layered.catalog
	@python3 scripts/verify/platform_kernel_baseline_guard.py

verify.owner.industry.isolation: guard.prod.forbid
	@python3 scripts/verify/owner_industry_isolation_probe.py

verify.owner.intent.non_intrusion: guard.prod.forbid
	@python3 scripts/verify/owner_intent_non_intrusion_guard.py

verify.capability.isolation.report: guard.prod.forbid
	@python3 scripts/verify/capability_isolation_report.py

verify.owner.scene.independent.deploy: guard.prod.forbid
	@python3 scripts/verify/owner_scene_independent_deploy_report.py

verify.platform.multi_domain.ready: guard.prod.forbid
	@python3 scripts/verify/platform_multi_domain_ready_report.py

verify.scene.conflict.stress: guard.prod.forbid
	@python3 scripts/verify/scene_conflict_stress_report.py

verify.capability.scale.stress: guard.prod.forbid
	@python3 scripts/verify/capability_scale_stress_report.py

verify.intent.concurrent.smoke: guard.prod.forbid
	@python3 scripts/verify/intent_concurrent_smoke_report.py

verify.p1.daily_business_visible_contract.audit: guard.prod.forbid
	@python3 scripts/verify/p1_daily_business_visible_contract_audit.py

.PHONY: verify.engineering_progress_income.visible_contract.audit
verify.engineering_progress_income.visible_contract.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/engineering_progress_income_visible_contract_audit.py

.PHONY: verify.formal_action.runtime_drift.audit
verify.formal_action.runtime_drift.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/formal_action_runtime_drift_audit.py

.PHONY: verify.user_confirmed.formal_surface.locked
verify.user_confirmed.formal_surface.locked: guard.prod.forbid verify.formal_surface.transition_field_audit verify.formal_config.p1_candidate_runtime_audit verify.user_formal_field.module_boundary.audit verify.formal_action.runtime_drift.audit verify.engineering_progress_income.visible_contract.audit verify.formal_entry_metadata.audit
	@echo "[OK] verify.user_confirmed.formal_surface.locked db=$(DB_NAME)"

.PHONY: verify.prepaid_tax.visible_surface_alignment.audit
verify.prepaid_tax.visible_surface_alignment.audit: guard.prod.forbid check-compose-project check-compose-env
	@if [[ -f "$(PREPAID_TAX_VISIBLE_XLSX)" ]]; then \
	  $(RUN_ENV) $(COMPOSE_BASE) cp "$(PREPAID_TAX_VISIBLE_XLSX)" "$(ODOO_SERVICE):/tmp/prepaid_tax_visible_alignment.xlsx"; \
	fi
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/prepaid_tax_visible_surface_alignment_audit.py

.PHONY: verify.input_invoice.visible_surface_alignment.audit
verify.input_invoice.visible_surface_alignment.audit: guard.prod.forbid check-compose-project check-compose-env
	@if [[ -f "$(INPUT_INVOICE_VISIBLE_XLSX)" ]]; then \
	  $(RUN_ENV) $(COMPOSE_BASE) cp "$(INPUT_INVOICE_VISIBLE_XLSX)" "$(ODOO_SERVICE):/tmp/input_invoice_visible_alignment.xlsx"; \
	fi
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/input_invoice_visible_surface_alignment_audit.py

.PHONY: verify.foreign_tax_certificate.visible_surface_alignment.audit
verify.foreign_tax_certificate.visible_surface_alignment.audit: guard.prod.forbid check-compose-project check-compose-env
	@if [[ -f "$(FOREIGN_TAX_CERTIFICATE_VISIBLE_XLSX)" ]]; then \
	  $(RUN_ENV) $(COMPOSE_BASE) cp "$(FOREIGN_TAX_CERTIFICATE_VISIBLE_XLSX)" "$(ODOO_SERVICE):/tmp/foreign_tax_certificate_visible_alignment.xlsx"; \
	fi
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/foreign_tax_certificate_visible_surface_alignment_audit.py

verify.p1.daily_business_form.usability.audit: guard.prod.forbid
	@python3 scripts/verify/p1_daily_business_form_usability_audit.py

verify.kernel.immutable.guard: guard.prod.forbid
	@python3 scripts/verify/kernel_immutable_guard.py

verify.kernel.freeze.guard: guard.prod.forbid
	@python3 scripts/verify/kernel_freeze_guard.py

verify.intent.public.surface.ready: guard.prod.forbid
	@python3 scripts/verify/intent_public_surface_ready_report.py

verify.platform.sla.guard: guard.prod.forbid
	@python3 scripts/verify/platform_sla_guard.py

verify.multi_tenant.evolution.smoke: guard.prod.forbid
	@python3 scripts/verify/multi_tenant_evolution_smoke.py

verify.contract.version.evolution.drill: guard.prod.forbid
	@python3 scripts/verify/contract_version_evolution_drill.py

verify.product.capability.matrix.ready: guard.prod.forbid
	@python3 scripts/verify/product_capability_matrix_ready.py

.PHONY: verify.capability.asset.map verify.scene.compression.model verify.scene.domain.taxonomy.guard verify.button.semantic.report verify.capability.dormant.explain.guard verify.phasex.p1
verify.capability.asset.map: guard.prod.forbid
	@python3 scripts/verify/capability_asset_map_report.py

verify.scene.compression.model: guard.prod.forbid
	@python3 scripts/verify/scene_compression_model_report.py

verify.scene.domain.taxonomy.guard: guard.prod.forbid
	@python3 scripts/verify/scene_domain_taxonomy_guard.py

verify.button.semantic.report: guard.prod.forbid
	@python3 scripts/verify/button_semantic_report.py

verify.capability.dormant.explain.guard: guard.prod.forbid
	@python3 scripts/verify/capability_dormant_explain_guard.py

verify.phasex.p1: guard.prod.forbid verify.capability.asset.map verify.scene.compression.model verify.scene.domain.taxonomy.guard verify.button.semantic.report verify.capability.dormant.explain.guard
	@echo "[OK] verify.phasex.p1 done"

.PHONY: verify.role.capability.diff.report verify.runtime.trend.report verify.catalog.runtime.explain.report verify.catalog.runtime.source.rules.guard verify.phasex.p2
verify.role.capability.diff.report: guard.prod.forbid
	@python3 scripts/verify/role_capability_diff_report.py

verify.runtime.trend.report: guard.prod.forbid
	@python3 scripts/verify/runtime_trend_report.py

verify.catalog.runtime.explain.report: guard.prod.forbid
	@python3 scripts/verify/catalog_runtime_explain_report.py

verify.catalog.runtime.source.rules.guard: guard.prod.forbid
	@python3 scripts/verify/catalog_runtime_source_rules_guard.py

verify.phasex.p2: guard.prod.forbid verify.role.capability.diff.report verify.runtime.trend.report verify.catalog.runtime.explain.report verify.catalog.runtime.source.rules.guard
	@echo "[OK] verify.phasex.p2 done"

.PHONY: verify.semantic.behavior.guard.report
verify.semantic.behavior.guard.report: guard.prod.forbid
	@python3 scripts/verify/semantic_behavior_guard_report.py

.PHONY: verify.product.capability.matrix.v2.report
verify.product.capability.matrix.v2.report: guard.prod.forbid
	@python3 scripts/verify/product_capability_matrix_v2_report.py

.PHONY: verify.stress.regression.policy.guard verify.system.stability.stress.regression
verify.stress.regression.policy.guard: guard.prod.forbid
	@python3 scripts/verify/stress_regression_policy_guard.py

verify.system.stability.stress.regression: guard.prod.forbid verify.stress.regression.policy.guard
	@python3 scripts/verify/system_stability_stress_regression.py

.PHONY: verify.sprint.week1.audit.report verify.sprint.week2.final.report
verify.sprint.week1.audit.report: guard.prod.forbid
	@$(MAKE) verify.capability.dormant.explain.guard
	@python3 scripts/verify/sprint_week1_audit_report.py

verify.sprint.week2.final.report: guard.prod.forbid
	@python3 scripts/verify/sprint_week2_final_report.py

.PHONY: verify.phasex.operating.summary
verify.phasex.operating.summary: guard.prod.forbid
	@python3 scripts/verify/phasex_operating_summary_report.py

verify.bundle.installation.ready: guard.prod.forbid
	@python3 scripts/verify/bundle_installation_ready.py
	@python3 scripts/verify/product_hardening_schema_guard.py --report bundle

.PHONY: verify.bundle.installation.ready.schema.guard
verify.bundle.installation.ready.schema.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/product_hardening_schema_guard.py
	@python3 scripts/verify/product_hardening_schema_guard.py --report bundle

verify.product.tier.ready: guard.prod.forbid
	@python3 scripts/verify/product_tier_ready.py

verify.ui.surface.stability.ready: guard.prod.forbid
	@python3 scripts/verify/ui_surface_stability_ready.py

verify.delivery.simulation.ready: guard.prod.forbid
	@python3 scripts/verify/delivery_simulation_ready.py

# prod-sim 全量隔离验证：适合发布前/环境漂移后（会重置并重建 sc_prod_sim）
.PHONY: verify.prod.sim.isolation
verify.prod.sim.isolation: guard.prod.forbid
	@echo "[verify.prod.sim.isolation] step=up"
	@$(MAKE) up \
		ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim \
		COMPOSE_FILES="-f $(COMPOSE_FILE_BASE) -f docker-compose.prod-sim.yml"
	@echo "[verify.prod.sim.isolation] step=demo.reset"
	@$(MAKE) demo.reset CODEX_MODE=gate \
		ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim \
		COMPOSE_FILES="-f $(COMPOSE_FILE_BASE) -f docker-compose.prod-sim.yml"
	@echo "[verify.prod.sim.isolation] step=odoo.recreate"
	@$(MAKE) odoo.recreate \
		ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim \
		COMPOSE_FILES="-f $(COMPOSE_FILE_BASE) -f docker-compose.prod-sim.yml"
	@echo "[verify.prod.sim.isolation] step=wait.odoo.ready"
	@bash -lc 'for i in $$(seq 1 30); do \
	  if curl -fsS --max-time 2 http://127.0.0.1:18069/web/login >/dev/null 2>/dev/null; then exit 0; fi; \
	  sleep 2; \
	done; \
	echo "❌ odoo not ready on :18069"; exit 2'
	@echo "[verify.prod.sim.isolation] step=delivery.simulation.ready"
	@E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo \
	$(MAKE) verify.delivery.simulation.ready \
		ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim
	@echo "[verify.prod.sim.isolation] PASS"

# prod-sim 快速隔离回归：适合日常联调（不 reset，仅健康检查 + e2e 验证）
.PHONY: verify.prod.sim.isolation.quick
verify.prod.sim.isolation.quick: guard.prod.forbid
	@echo "[verify.prod.sim.isolation.quick] step=up"
	@$(MAKE) up \
		ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim \
		COMPOSE_FILES="-f $(COMPOSE_FILE_BASE) -f docker-compose.prod-sim.yml"
	@echo "[verify.prod.sim.isolation.quick] step=wait.odoo.ready"
	@bash -lc 'for i in $$(seq 1 30); do \
	  if curl -fsS --max-time 2 http://127.0.0.1:18069/web/login >/dev/null 2>/dev/null; then exit 0; fi; \
	  sleep 2; \
	done; \
	echo "❌ odoo not ready on :18069"; exit 2'
	@echo "[verify.prod.sim.isolation.quick] step=delivery.simulation.ready"
	@E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo \
	$(MAKE) verify.delivery.simulation.ready \
		ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim
	@echo "[verify.prod.sim.isolation.quick] PASS"

.PHONY: verify.prod.sim.acceptance.evidence.schema.guard
verify.prod.sim.acceptance.evidence.schema.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/prod_sim_acceptance_evidence_schema_guard.py
	@python3 scripts/verify/prod_sim_acceptance_evidence_schema_guard.py

.PHONY: verify.production_deployment.record.guard
verify.production_deployment.record.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/production_deployment_record_guard.py
	@python3 scripts/verify/production_deployment_record_guard.py

.PHONY: verify.production_release.flow.guard
verify.production_release.flow.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/production_release_flow_guard.py
	@python3 scripts/verify/production_release_flow_guard.py

.PHONY: verify.production_git.authority.guard
verify.production_git.authority.guard:
	@python3 -m py_compile scripts/verify/production_git_authority_guard.py
	@python3 scripts/verify/production_git_authority_guard.py


.PHONY: verify.product.delivery.gap
verify.product.delivery.gap: guard.prod.forbid
	@python3 scripts/verify/product_delivery_gap_report.py

.PHONY: verify.product.delivery.productization.readiness
verify.product.delivery.productization.readiness: guard.prod.forbid
	@python3 scripts/verify/product_delivery_productization_readiness.py

.PHONY: verify.product.delivery.productization.readiness.strict
verify.product.delivery.productization.readiness.strict: guard.prod.forbid
	@python3 scripts/verify/product_delivery_productization_readiness.py --strict

.PHONY: verify.product.delivery.v1.map
verify.product.delivery.v1.map: guard.prod.forbid
	@python3 scripts/verify/module_scene_capability_map_report.py

.PHONY: verify.phasea.a0a1
verify.phasea.a0a1: guard.prod.forbid verify.product.delivery.v1.map
	@echo "[OK] verify.phasea.a0a1 done"

.PHONY: verify.product.delivery.journeys
verify.product.delivery.journeys: guard.prod.forbid
	@python3 scripts/verify/delivery_user_journey_guard.py

.PHONY: verify.product.delivery.roles
verify.product.delivery.roles: guard.prod.forbid
	@python3 scripts/verify/role_capability_profiles_export.py
	@python3 scripts/verify/role_home_openability_report.py

.PHONY: verify.product.delivery.role_home_openability
verify.product.delivery.role_home_openability: guard.prod.forbid
	@python3 scripts/verify/role_home_openability_report.py

.PHONY: verify.product.delivery.visibility
verify.product.delivery.visibility: guard.prod.forbid
	@python3 scripts/verify/visibility_filter_verification.py

.PHONY: verify.product.delivery.demo_data verify.demo.release.seed
verify.product.delivery.demo_data: guard.prod.forbid
	@python3 scripts/verify/demo_data_presence_report.py

verify.demo.release.seed: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/demo_release_seed.sh

.PHONY: verify.product.delivery.execute_button_whitelist
verify.product.delivery.execute_button_whitelist: guard.prod.forbid
	@python3 scripts/verify/execute_button_whitelist_verification.py

.PHONY: verify.product.delivery.menu
verify.product.delivery.menu: guard.prod.forbid
	@python3 scripts/verify/delivery_menu_tree_report.py

.PHONY: verify.product.menu.catalog
verify.product.menu.catalog: guard.prod.forbid check-compose-project check-compose-env
	@mkdir -p artifacts/product docs/product
	@python3 -m py_compile scripts/verify/product_menu_catalog_runtime_audit.py scripts/verify/product_menu_catalog_report.py scripts/verify/product_menu_blueprint_report.py
	@$(RUN_ENV) PRODUCT_MENU_CATALOG_RUNTIME_PATH=/tmp/product_menu_catalog_runtime_v1.json DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/product_menu_catalog_runtime_audit.py
	@$(RUN_ENV) $(COMPOSE_BASE) cp $(ODOO_SERVICE):/tmp/product_menu_catalog_runtime_v1.json artifacts/product/product_menu_catalog_runtime_v1.json >/dev/null
	@python3 scripts/verify/product_menu_catalog_report.py
	@python3 scripts/verify/product_menu_blueprint_report.py

.PHONY: verify.system_init.menu_boundary.guard
verify.system_init.menu_boundary.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/system_init_menu_boundary_guard.py
	@python3 scripts/verify/system_init_menu_boundary_guard.py

.PHONY: verify.release.phase1.navigation_convergence.guard
verify.release.phase1.navigation_convergence.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/release_phase1_navigation_convergence_guard.py
	@python3 scripts/verify/release_phase1_navigation_convergence_guard.py

.PHONY: verify.release.phase2.core_scenarios_closure.guard
verify.release.phase2.core_scenarios_closure.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/release_phase2_core_scenarios_closure_guard.py
	@python3 scripts/verify/release_phase2_core_scenarios_closure_guard.py

.PHONY: verify.release.phase6.launch_closeout.guard
verify.release.phase6.launch_closeout.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/release_phase6_launch_closeout_guard.py
	@python3 scripts/verify/release_phase6_launch_closeout_guard.py

.PHONY: verify.release.user_acceptance.closeout.guard
verify.release.user_acceptance.closeout.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/release_user_acceptance_closeout_guard.py
	@python3 scripts/verify/release_user_acceptance_closeout_guard.py

.PHONY: verify.release.round1.final_closeout.guard
verify.release.round1.final_closeout.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/release_round1_final_closeout_guard.py
	@python3 scripts/verify/release_round1_final_closeout_guard.py

.PHONY: verify.release.master_stage.final_closeout.guard
verify.release.master_stage.final_closeout.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/release_master_stage_final_closeout_guard.py
	@python3 scripts/verify/release_master_stage_final_closeout_guard.py

.PHONY: verify.release.delivery_9_module.final_closeout.guard
verify.release.delivery_9_module.final_closeout.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/delivery_9_module_final_closeout_guard.py
	@python3 scripts/verify/delivery_9_module_final_closeout_guard.py

.PHONY: verify.release.current_status.wording_closeout.guard
verify.release.current_status.wording_closeout.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/release_current_status_wording_closeout_guard.py
	@python3 scripts/verify/release_current_status_wording_closeout_guard.py

.PHONY: verify.product.delivery.scoreboard.final_closeout.guard
verify.product.delivery.scoreboard.final_closeout.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/product_delivery_scoreboard_final_closeout_guard.py
	@python3 scripts/verify/product_delivery_scoreboard_final_closeout_guard.py

.PHONY: verify.product.menu.release.ready
verify.product.menu.release.ready: guard.prod.forbid \
	verify.product.menu.catalog \
	verify.system_init.menu_boundary.guard \
	verify.platform.release_policy.runtime \
	verify.product.surface.clean
	@echo "[OK] verify.product.menu.release.ready done"

.PHONY: verify.product.delivery.freshness
verify.product.delivery.freshness: guard.prod.forbid
	@python3 scripts/verify/product_delivery_freshness_guard.py

.PHONY: verify.product.delivery.governance_truth
verify.product.delivery.governance_truth: guard.prod.forbid
	@status=0; python3 scripts/verify/product_delivery_governance_truth_guard.py || status=$$?; \
	schema_status=0; python3 scripts/verify/product_delivery_governance_truth_schema_guard.py || schema_status=$$?; \
	if [ "$$status" -eq 0 ]; then status=$$schema_status; fi; \
	exit $$status

.PHONY: verify.product.delivery.governance_truth.schema.guard
verify.product.delivery.governance_truth.schema.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/product_delivery_governance_truth_schema_guard.py
	@python3 scripts/verify/product_delivery_governance_truth_schema_guard.py

.PHONY: verify.product.delivery.action_closure.smoke
verify.product.delivery.action_closure.smoke: guard.prod.forbid
	@python3 scripts/verify/product_delivery_action_closure_smoke.py
	@python3 scripts/verify/product_delivery_smoke_schema_guard.py --report action

.PHONY: verify.product.delivery.action_closure.schema.guard
verify.product.delivery.action_closure.schema.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/product_delivery_smoke_schema_guard.py
	@python3 scripts/verify/product_delivery_smoke_schema_guard.py --report action

.PHONY: verify.delivery.payment_approval.chain_summary
verify.delivery.payment_approval.chain_summary: guard.prod.forbid
	@python3 scripts/verify/payment_request_approval_chain_summary.py

.PHONY: verify.delivery.project_task.action_smoke
verify.delivery.project_task.action_smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) ROLE_PM_LOGIN=$(or $(ROLE_PM_LOGIN),demo_role_pm) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/project_task_action_seed.py
	@python3 scripts/verify/project_task_action_smoke.py

.PHONY: verify.delivery.project_journey.trace_archive
verify.delivery.project_journey.trace_archive: guard.prod.forbid verify.delivery.journey.role_matrix.guard verify.delivery.project_task.action_smoke
	@python3 scripts/verify/project_journey_trace_archive.py

.PHONY: verify.delivery.material.action_replay
verify.delivery.material.action_replay: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) ROLE_MATERIAL_LOGIN=$(or $(ROLE_MATERIAL_LOGIN),demo_business_full) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/material_action_replay_seed.py
	@ROLE_MATERIAL_LOGIN=$(or $(ROLE_MATERIAL_LOGIN),demo_business_full) python3 scripts/verify/material_action_replay_smoke.py

.PHONY: verify.delivery.material.cross_document_progress
verify.delivery.material.cross_document_progress: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/material_settlement_payment_execution_traceability_audit.py

.PHONY: verify.delivery.executive.readonly
verify.delivery.executive.readonly: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) ROLE_EXECUTIVE_READONLY_LOGIN=$(or $(ROLE_EXECUTIVE_READONLY_LOGIN),executive_readonly_smoke) ROLE_EXECUTIVE_READONLY_PASSWORD=$(or $(ROLE_EXECUTIVE_READONLY_PASSWORD),demo) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/executive_readonly_seed.py
	@ROLE_EXECUTIVE_READONLY_LOGIN=$(or $(ROLE_EXECUTIVE_READONLY_LOGIN),executive_readonly_smoke) ROLE_EXECUTIVE_READONLY_PASSWORD=$(or $(ROLE_EXECUTIVE_READONLY_PASSWORD),demo) python3 scripts/verify/executive_readonly_smoke.py

.PHONY: verify.delivery.ledger.snapshot
verify.delivery.ledger.snapshot: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) ROLE_LEDGER_READONLY_LOGIN=$(or $(ROLE_LEDGER_READONLY_LOGIN),ledger_readonly_smoke) ROLE_LEDGER_READONLY_PASSWORD=$(or $(ROLE_LEDGER_READONLY_PASSWORD),demo) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/ledger_snapshot_seed.py
	@ROLE_LEDGER_READONLY_LOGIN=$(or $(ROLE_LEDGER_READONLY_LOGIN),ledger_readonly_smoke) ROLE_LEDGER_READONLY_PASSWORD=$(or $(ROLE_LEDGER_READONLY_PASSWORD),demo) python3 scripts/verify/ledger_snapshot_smoke.py

.PHONY: verify.delivery.ledger.reconciliation_trend
verify.delivery.ledger.reconciliation_trend: guard.prod.forbid verify.delivery.ledger.snapshot
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/ledger_reconciliation_trend.py

.PHONY: verify.delivery.cost.search_pagination
verify.delivery.cost.search_pagination: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) ROLE_COST_READONLY_LOGIN=$(or $(ROLE_COST_READONLY_LOGIN),cost_readonly_smoke) ROLE_COST_READONLY_PASSWORD=$(or $(ROLE_COST_READONLY_PASSWORD),demo) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/cost_search_pagination_seed.py
	@ROLE_COST_READONLY_LOGIN=$(or $(ROLE_COST_READONLY_LOGIN),cost_readonly_smoke) ROLE_COST_READONLY_PASSWORD=$(or $(ROLE_COST_READONLY_PASSWORD),demo) python3 scripts/verify/cost_search_pagination_smoke.py

.PHONY: verify.delivery.quality_safety.closure
verify.delivery.quality_safety.closure: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/site_quality_safety_closure_audit.py

.PHONY: verify.delivery.lifecycle.audit_export
verify.delivery.lifecycle.audit_export: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/lifecycle_audit_export.py

.PHONY: verify.delivery.default_scene.semantic_monitor
verify.delivery.default_scene.semantic_monitor: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/default_scene_semantic_monitor.py

.PHONY: verify.product.delivery.module_capability.smoke verify.product.delivery.module9.smoke
verify.product.delivery.module_capability.smoke: guard.prod.forbid
	@python3 scripts/verify/product_delivery_module9_smoke.py
	@python3 scripts/verify/product_delivery_smoke_schema_guard.py --report module

.PHONY: verify.product.delivery.module_capability.schema.guard
verify.product.delivery.module_capability.schema.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/product_delivery_smoke_schema_guard.py
	@python3 scripts/verify/product_delivery_smoke_schema_guard.py --report module

verify.product.delivery.module9.smoke: verify.product.delivery.module_capability.smoke

.PHONY: verify.backend.contract.closure.guard
verify.backend.contract.closure.guard: guard.prod.forbid
	@python3 scripts/verify/backend_contract_closure_guard.py
	@python3 scripts/verify/backend_contract_closure_snapshot_guard.py
	@python3 scripts/verify/backend_contract_closure_snapshot_schema_guard.py
	@python3 scripts/verify/intent_canonical_alias_snapshot_guard.py

.PHONY: verify.backend.contract.closure.snapshot.guard
verify.backend.contract.closure.snapshot.guard: guard.prod.forbid
	@python3 scripts/verify/backend_contract_closure_snapshot_guard.py
	@python3 scripts/verify/backend_contract_closure_snapshot_schema_guard.py

.PHONY: verify.backend.contract.closure.snapshot.schema.guard
verify.backend.contract.closure.snapshot.schema.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/backend_contract_closure_snapshot_schema_guard.py
	@python3 scripts/verify/backend_contract_closure_snapshot_schema_guard.py

.PHONY: verify.intent.canonical_alias.snapshot.guard
verify.intent.canonical_alias.snapshot.guard: guard.prod.forbid
	@python3 scripts/verify/intent_canonical_alias_snapshot_guard.py
	@python3 scripts/verify/intent_canonical_alias_snapshot_schema_guard.py

.PHONY: verify.intent.canonical_alias.snapshot.schema.guard
verify.intent.canonical_alias.snapshot.schema.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/intent_canonical_alias_snapshot_schema_guard.py
	@python3 scripts/verify/intent_canonical_alias_snapshot_schema_guard.py

.PHONY: verify.backend.contract.closure.mainline
verify.backend.contract.closure.mainline: guard.prod.forbid
	@STRUCTURE=PASS; SNAPSHOT=PASS; ALIAS=PASS; \
	echo "[verify.backend.contract.closure.mainline] step=closure_structure_guard"; \
	if ! python3 scripts/verify/backend_contract_closure_guard.py; then STRUCTURE=FAIL; fi; \
	echo "[verify.backend.contract.closure.mainline] step=closure_snapshot_guard"; \
	if ! python3 scripts/verify/backend_contract_closure_snapshot_guard.py; then SNAPSHOT=FAIL; fi; \
	if ! python3 scripts/verify/backend_contract_closure_snapshot_schema_guard.py; then SNAPSHOT=FAIL; fi; \
	echo "[verify.backend.contract.closure.mainline] step=intent_alias_snapshot_guard"; \
	if ! python3 scripts/verify/intent_canonical_alias_snapshot_guard.py; then ALIAS=FAIL; fi; \
	python3 scripts/verify/backend_contract_closure_mainline_summary.py --structure $$STRUCTURE --snapshot $$SNAPSHOT --alias $$ALIAS; \
	python3 scripts/verify/backend_contract_closure_mainline_summary_schema_guard.py; \
	if [ "$$STRUCTURE" = "PASS" ] && [ "$$SNAPSHOT" = "PASS" ] && [ "$$ALIAS" = "PASS" ]; then \
	  echo "[OK] verify.backend.contract.closure.mainline done"; \
	else \
	  echo "[FAIL] verify.backend.contract.closure.mainline"; \
	  exit 1; \
	fi

.PHONY: verify.backend.contract.closure.mainline.summary.schema.guard
verify.backend.contract.closure.mainline.summary.schema.guard: guard.prod.forbid
	@python3 scripts/verify/backend_contract_closure_mainline_summary_schema_guard.py

.PHONY: verify.product.delivery.ready
verify.product.delivery.ready: guard.prod.forbid verify.product.delivery.gap verify.product.delivery.freshness verify.product.delivery.governance_truth verify.product.delivery.productization.readiness.strict
	@echo "[OK] verify.product.delivery.ready done"

.PHONY: verify.restricted verify.product.delivery.mainline
verify.restricted: guard.prod.forbid
	@echo "[verify.restricted] profile=restricted entry=verify.product.delivery.mainline"
	@CI_SCENE_DELIVERY_PROFILE=restricted $(MAKE) --no-print-directory verify.product.delivery.mainline

verify.product.delivery.mainline: guard.prod.forbid
	@PROFILE=$${CI_SCENE_DELIVERY_PROFILE:-restricted}; \
	FRONTEND_STATUS=PASS; SCENE_STATUS=PASS; ACTION_STATUS=PASS; MODULE9_STATUS=PASS; CONTRACT_CLOSURE_STATUS=PASS; GOVERNANCE_STATUS=PASS; \
	echo "[verify.product.delivery.mainline] step=frontend_gate"; \
	if ! pnpm -C frontend gate; then FRONTEND_STATUS=FAIL; fi; \
	echo "[verify.product.delivery.mainline] step=scene_delivery_readiness profile=$$PROFILE"; \
	if [ "$$FRONTEND_STATUS" = "PASS" ]; then \
	  if ! CI_SCENE_DELIVERY_PROFILE=$$PROFILE SC_MULTI_COMPANY_EVIDENCE_STRICT=1 $(MAKE) --no-print-directory ci.scene.delivery.readiness; then \
	    SCENE_STATUS=FAIL; \
	  fi; \
	else \
	  SCENE_STATUS=SKIP; \
	fi; \
	echo "[verify.product.delivery.mainline] step=action_closure_smoke"; \
	if [ "$$SCENE_STATUS" = "PASS" ]; then \
	  if ! $(MAKE) --no-print-directory verify.product.delivery.action_closure.smoke; then ACTION_STATUS=FAIL; fi; \
	else \
	  ACTION_STATUS=SKIP; \
	fi; \
	echo "[verify.product.delivery.mainline] step=module_capability_smoke"; \
	if [ "$$ACTION_STATUS" = "PASS" ]; then \
	  if ! $(MAKE) --no-print-directory verify.product.delivery.module_capability.smoke; then MODULE9_STATUS=FAIL; fi; \
	else \
	  MODULE9_STATUS=SKIP; \
	fi; \
	echo "[verify.product.delivery.mainline] step=backend_contract_closure_mainline"; \
	if [ "$$MODULE9_STATUS" = "PASS" ]; then \
	  if ! $(MAKE) --no-print-directory verify.backend.contract.closure.mainline; then CONTRACT_CLOSURE_STATUS=FAIL; fi; \
	else \
	  CONTRACT_CLOSURE_STATUS=SKIP; \
	fi; \
	echo "[verify.product.delivery.mainline] step=governance_truth"; \
	if ! $(MAKE) --no-print-directory verify.product.delivery.governance_truth; then GOVERNANCE_STATUS=FAIL; fi; \
	echo "[verify.product.delivery.mainline] contract_closure_guard=$$CONTRACT_CLOSURE_STATUS"; \
	python3 scripts/verify/delivery_mainline_run_summary.py \
	  --profile $$PROFILE \
	  --frontend $$FRONTEND_STATUS \
	  --scene $$SCENE_STATUS \
	  --action-closure $$ACTION_STATUS \
	  --module-capability $$MODULE9_STATUS \
	  --governance $$GOVERNANCE_STATUS; \
	python3 scripts/verify/delivery_mainline_run_summary_schema_guard.py; \
		$(MAKE) --no-print-directory refresh.delivery.readiness.scoreboard >/dev/null; \
		python3 -c "import json, pathlib; p=pathlib.Path('artifacts/backend/delivery_readiness_ci_summary.json'); d=json.loads(p.read_text(encoding='utf-8')) if p.is_file() else {}; o=d.get('overall') if isinstance(d.get('overall'), dict) else {}; print(f\"[verify.product.delivery.mainline] overall_ok={o.get('ok')} policy={o.get('policy')}\")"; \
	if [ "$$FRONTEND_STATUS" = "PASS" ] && [ "$$SCENE_STATUS" = "PASS" ] && [ "$$ACTION_STATUS" = "PASS" ] && [ "$$MODULE9_STATUS" = "PASS" ] && [ "$$CONTRACT_CLOSURE_STATUS" = "PASS" ] && [ "$$GOVERNANCE_STATUS" = "PASS" ]; then \
	  echo "[OK] verify.product.delivery.mainline done"; \
	else \
	  echo "[FAIL] verify.product.delivery.mainline"; \
	  exit 1; \
	fi

.PHONY: verify.product.delivery.mainline.summary.schema.guard
verify.product.delivery.mainline.summary.schema.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/delivery_mainline_run_summary_schema_guard.py
	@python3 scripts/verify/delivery_mainline_run_summary_schema_guard.py

.PHONY: export.product.delivery.package
export.product.delivery.package: guard.prod.forbid
	@python3 scripts/verify/product_delivery_package_manifest.py

verify.complexity.guard: guard.prod.forbid
	@python3 scripts/verify/complexity_guard.py

export.product.documentation: guard.prod.forbid
	@python3 scripts/verify/export_product_documentation.py

verify.product.tier.coverage: guard.prod.forbid
	@python3 scripts/verify/product_tier_coverage.py

seed.delivery.minimum: guard.prod.forbid
	@python3 scripts/verify/seed_delivery_minimum.py

verify.delivery.business.success.ready: guard.prod.forbid seed.delivery.minimum
	@python3 scripts/verify/delivery_business_success_ready.py

verify.runtime_contract.test_placeholder.guard: guard.prod.forbid check-compose-project check-compose-env
	@mkdir -p artifacts/backend
	@$(RUN_ENV) RUNTIME_CONTRACT_TEST_PLACEHOLDER_GUARD_PATH=/tmp/runtime_contract_test_placeholder_guard.json DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/runtime_contract_test_placeholder_guard.py
	@$(RUN_ENV) $(COMPOSE_BASE) cp $(ODOO_SERVICE):/tmp/runtime_contract_test_placeholder_guard.json artifacts/backend/runtime_contract_test_placeholder_guard.json >/dev/null

.PHONY: verify.lowcode_config.boundary.guard
verify.lowcode_config.boundary.guard: guard.prod.forbid verify.business_config.guard_inventory verify.smart_core.boundary_guard verify.app_config_engine.boundary_guard verify.view.orchestration_product_boundary_guard verify.view.orchestration_boundary_guard verify.lowcode_config.customer_module_asset.replay.guard
	@python3 -m py_compile scripts/verify/lowcode_config_boundary_guard.py
	@python3 scripts/verify/lowcode_config_boundary_guard.py

.PHONY: verify.lowcode_config.customer_baseline.candidate
verify.lowcode_config.customer_baseline.candidate: guard.prod.forbid check-compose-project check-compose-env
	@mkdir -p artifacts/backend
	@python3 -m py_compile scripts/verify/lowcode_customer_config_baseline_candidate.py
	@$(RUN_ENV) LOWCODE_CUSTOMER_CONFIG_BASELINE_CANDIDATE_PATH=/tmp/lowcode_customer_config_baseline_candidate.json DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/lowcode_customer_config_baseline_candidate.py
	@$(RUN_ENV) $(COMPOSE_BASE) cp $(ODOO_SERVICE):/tmp/lowcode_customer_config_baseline_candidate.json artifacts/backend/lowcode_customer_config_baseline_candidate.json >/dev/null

.PHONY: verify.lowcode_config.customer_module_asset.draft
verify.lowcode_config.customer_module_asset.draft: verify.lowcode_config.customer_baseline.candidate
	@python3 -m py_compile scripts/verify/lowcode_customer_config_module_asset_draft.py
	@LOWCODE_CUSTOMER_CONFIG_BASELINE_CANDIDATE_INPUT=artifacts/backend/lowcode_customer_config_baseline_candidate.json LOWCODE_CUSTOMER_CONFIG_MODULE_ASSET_DRAFT_PATH=artifacts/backend/lowcode_customer_config_module_asset_draft.json python3 scripts/verify/lowcode_customer_config_module_asset_draft.py

.PHONY: verify.lowcode_config.customer_module_asset.acceptance_template
verify.lowcode_config.customer_module_asset.acceptance_template: verify.lowcode_config.customer_module_asset.draft
	@python3 -m py_compile scripts/verify/lowcode_customer_config_acceptance_decision_template.py
	@LOWCODE_CUSTOMER_CONFIG_MODULE_ASSET_DRAFT_INPUT=artifacts/backend/lowcode_customer_config_module_asset_draft.json LOWCODE_CUSTOMER_CONFIG_ACCEPTANCE_DECISION_TEMPLATE_PATH=artifacts/backend/lowcode_customer_config_acceptance_decisions_template.json python3 scripts/verify/lowcode_customer_config_acceptance_decision_template.py

.PHONY: verify.lowcode_config.customer_module_asset.acceptance_apply.dry_run
verify.lowcode_config.customer_module_asset.acceptance_apply.dry_run: verify.lowcode_config.customer_module_asset.acceptance_template
	@python3 -m py_compile scripts/verify/lowcode_customer_config_apply_acceptance_decisions.py scripts/verify/lowcode_customer_config_apply_acceptance_decisions_test.py
	@python3 scripts/verify/lowcode_customer_config_apply_acceptance_decisions_test.py
	@LOWCODE_CUSTOMER_CONFIG_MODULE_ASSET_DRAFT_INPUT=artifacts/backend/lowcode_customer_config_module_asset_draft.json LOWCODE_CUSTOMER_CONFIG_ACCEPTANCE_DECISIONS_INPUT=artifacts/backend/lowcode_customer_config_acceptance_decisions_template.json LOWCODE_CUSTOMER_CONFIG_ACCEPTED_ASSET_OUTPUT=artifacts/backend/lowcode_customer_config_contracts_candidate.json python3 scripts/verify/lowcode_customer_config_apply_acceptance_decisions.py

.PHONY: verify.lowcode_config.customer_module_asset.pipeline
verify.lowcode_config.customer_module_asset.pipeline: verify.lowcode_config.customer_module_asset.acceptance_apply.dry_run verify.lowcode_config.customer_module_asset.replay.guard
	@echo "[lowcode_customer_config_pipeline] PASS"

.PHONY: verify.lowcode_config.customer_module_asset.release_hardening.guard
verify.lowcode_config.customer_module_asset.release_hardening.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/lowcode_customer_config_release_hardening_guard.py
	@python3 scripts/verify/lowcode_customer_config_release_hardening_guard.py

.PHONY: verify.lowcode_config.customer_module_asset.replay.guard
verify.lowcode_config.customer_module_asset.replay.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/lowcode_customer_config_module_asset_replay_guard.py
	@python3 scripts/verify/lowcode_customer_config_module_asset_replay_guard.py

.PHONY: verify.lowcode_config.runtime_boundary.guard
verify.lowcode_config.runtime_boundary.guard: guard.prod.forbid check-compose-project check-compose-env
	@mkdir -p artifacts/backend
	@$(RUN_ENV) LOWCODE_CONFIG_RUNTIME_SOURCE_STATUS_STRICT=1 BUSINESS_CONFIG_LOWCODE_RUNTIME_BOUNDARY_GUARD_PATH=/tmp/lowcode_config_runtime_boundary_guard.json DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/lowcode_config_runtime_boundary_guard.py
	@$(RUN_ENV) $(COMPOSE_BASE) cp $(ODOO_SERVICE):/tmp/lowcode_config_runtime_boundary_guard.json artifacts/backend/lowcode_config_runtime_boundary_guard.json >/dev/null

.PHONY: verify.product.no_demo_data
verify.product.no_demo_data: guard.prod.forbid check-compose-project check-compose-env
	@mkdir -p artifacts/backend
	@status=0; \
	$(RUN_ENV) PRODUCT_REQUIRE_NO_DEMO_DATA=1 \
		NON_DEMO_DATA_CONTAMINATION_GUARD_JSON=/tmp/non_demo_data_contamination_guard.json \
		NON_DEMO_DATA_CONTAMINATION_GUARD_MD=/tmp/non_demo_data_contamination_guard.md \
		DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/non_demo_data_contamination_guard.py || status=$$?; \
	$(RUN_ENV) $(COMPOSE_BASE) cp $(ODOO_SERVICE):/tmp/non_demo_data_contamination_guard.json artifacts/backend/non_demo_data_contamination_guard.json >/dev/null 2>&1 || true; \
	$(RUN_ENV) $(COMPOSE_BASE) cp $(ODOO_SERVICE):/tmp/non_demo_data_contamination_guard.md artifacts/backend/non_demo_data_contamination_guard.md >/dev/null 2>&1 || true; \
	schema_status=0; python3 scripts/verify/non_demo_data_contamination_guard_schema_guard.py || schema_status=$$?; \
	if [ "$$status" -eq 0 ]; then status=$$schema_status; fi; \
	exit $$status

.PHONY: verify.product.no_demo_data.schema.guard
verify.product.no_demo_data.schema.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/non_demo_data_contamination_guard_schema_guard.py
	@python3 scripts/verify/non_demo_data_contamination_guard_schema_guard.py

verify.product.surface.clean: guard.prod.forbid verify.product.capability.matrix.ready verify.runtime_contract.test_placeholder.guard verify.lowcode_config.boundary.guard verify.lowcode_config.runtime_boundary.guard verify.business_config.snapshot verify.product.no_demo_data
	@echo "[OK] verify.product.surface.clean done"

verify.product.complexity.bound: guard.prod.forbid verify.complexity.guard
	@echo "[OK] verify.product.complexity.bound done"

verify.product.bundle.isolation: guard.prod.forbid verify.bundle.installation.ready
	@echo "[OK] verify.product.bundle.isolation done"

verify.product.tier.enforcement: guard.prod.forbid verify.product.tier.coverage
	@echo "[OK] verify.product.tier.enforcement done"

verify.ui.product.stability: guard.prod.forbid verify.ui.surface.stability.ready
	@echo "[OK] verify.ui.product.stability done"

verify.delivery.reproducible: guard.prod.forbid verify.delivery.business.success.ready
	@echo "[OK] verify.delivery.reproducible done"

verify.product.sla.baseline: guard.prod.forbid verify.platform.performance.smoke
	@echo "[OK] verify.product.sla.baseline done"

verify.product.release.ready: guard.prod.forbid \
	verify.docs.product_boundary \
	verify.industry_module.product_boundary \
	verify.user_module.product_boundary \
	verify.lowcode_config.customer_module_asset.pipeline \
	verify.lowcode_config.customer_module_asset.release_hardening.guard \
	verify.product.surface.clean \
	verify.product.menu.release.ready \
	verify.product.complexity.bound \
	verify.product.bundle.isolation \
	verify.product.tier.enforcement \
	verify.product.delivery.productization.readiness.strict \
	verify.frontend.widget_richness.post_ga.guard \
	verify.ui.product.stability \
	verify.delivery.reproducible \
	verify.product.sla.baseline
	@echo "[OK] verify.product.release.ready done"

.PHONY: verify.platform.release_policy.runtime
verify.platform.release_policy.runtime: guard.prod.forbid check-compose-project check-compose-env
	@mkdir -p artifacts/backend
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/platform_release_policy_runtime_probe.py
	@$(RUN_ENV) $(COMPOSE_BASE) cp $(ODOO_SERVICE):/tmp/platform_release_policy_runtime_probe.json artifacts/backend/platform_release_policy_runtime_probe.json >/dev/null
	@$(RUN_ENV) $(COMPOSE_BASE) cp $(ODOO_SERVICE):/tmp/platform_release_policy_runtime_probe.md artifacts/backend/platform_release_policy_runtime_probe.md >/dev/null
	@python3 scripts/verify/platform_release_policy_runtime_schema_guard.py

.PHONY: verify.platform.release_policy.runtime.schema.guard
verify.platform.release_policy.runtime.schema.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/platform_release_policy_runtime_schema_guard.py
	@python3 scripts/verify/platform_release_policy_runtime_schema_guard.py

.PHONY: verify.release.v2_0_0.preflight
verify.release.v2_0_0.preflight: guard.prod.forbid \
	verify.system.capability_baseline.report \
	verify.platform.release_policy.runtime \
	verify.backend.contract.closure.mainline \
	verify.restricted
	@echo "[OK] verify.release.v2_0_0.preflight done"

.PHONY: verify.release.v2_0_0.product_hardening
verify.release.v2_0_0.product_hardening: guard.prod.forbid verify.product.release.ready
	@echo "[OK] verify.release.v2_0_0.product_hardening done"

.PHONY: verify.release.v2_0_0.checklist.guard
verify.release.v2_0_0.checklist.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/release_v2_0_0_checklist_guard.py
	@python3 scripts/verify/release_v2_0_0_checklist_guard.py

.PHONY: verify.release.v2_0_0.evidence_manifest.guard
verify.release.v2_0_0.evidence_manifest.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/release_v2_0_0_evidence_manifest_guard.py
	@python3 scripts/verify/release_v2_0_0_evidence_manifest_guard.py

.PHONY: verify.release.v2_0_0.control_docs.guard
verify.release.v2_0_0.control_docs.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/release_v2_0_0_control_docs_guard.py
	@python3 scripts/verify/release_v2_0_0_control_docs_guard.py

.PHONY: verify.release.v2_0_0.governance.guard
verify.release.v2_0_0.governance.guard: guard.prod.forbid \
	verify.release.v2_0_0.control_docs.guard \
	verify.release.v2_0_0.evidence_manifest.guard \
	verify.release.v2_0_0.checklist.guard \
	verify.production_release.flow.guard
	@echo "[OK] verify.release.v2_0_0.governance.guard done"

.PHONY: verify.release.v2_0_0.formal_evidence.schema.guard
verify.release.v2_0_0.formal_evidence.schema.guard: guard.prod.forbid \
	verify.release.v2_0_0.governance.guard \
	verify.bundle.installation.ready.schema.guard \
	verify.platform.performance.smoke.schema.guard \
	verify.dev.acceptance.release.schema.guard \
	verify.prod.sim.acceptance.evidence.schema.guard
	@echo "[OK] verify.release.v2_0_0.formal_evidence.schema.guard done"

.PHONY: verify.release_v2_0_0.preflight verify.release_v2_0_0.product_hardening verify.release_v2_0_0.checklist.guard verify.release_v2_0_0.evidence_manifest.guard verify.release_v2_0_0.control_docs.guard verify.release_v2_0_0.governance.guard verify.release_v2_0_0.formal_evidence.schema.guard
verify.release_v2_0_0.preflight: verify.release.v2_0_0.preflight
	@echo "[alias] use verify.release.v2_0_0.preflight"
verify.release_v2_0_0.product_hardening: verify.release.v2_0_0.product_hardening
	@echo "[alias] use verify.release.v2_0_0.product_hardening"
verify.release_v2_0_0.checklist.guard: verify.release.v2_0_0.checklist.guard
	@echo "[alias] use verify.release.v2_0_0.checklist.guard"
verify.release_v2_0_0.evidence_manifest.guard: verify.release.v2_0_0.evidence_manifest.guard
	@echo "[alias] use verify.release.v2_0_0.evidence_manifest.guard"
verify.release_v2_0_0.control_docs.guard: verify.release.v2_0_0.control_docs.guard
	@echo "[alias] use verify.release.v2_0_0.control_docs.guard"
verify.release_v2_0_0.governance.guard: verify.release.v2_0_0.governance.guard
	@echo "[alias] use verify.release.v2_0_0.governance.guard"
verify.release_v2_0_0.formal_evidence.schema.guard: verify.release.v2_0_0.formal_evidence.schema.guard
	@echo "[alias] use verify.release.v2_0_0.formal_evidence.schema.guard"

verify.platform.distribution.report: guard.prod.forbid
	@python3 scripts/verify/platform_distribution_ready_report.py

verify.platform.distribution.ready: guard.prod.forbid \
	verify.owner.industry.isolation \
	verify.owner.intent.non_intrusion \
	verify.capability.isolation.report \
	verify.owner.scene.independent.deploy \
	verify.platform.distribution.report
	@echo "[OK] verify.platform.distribution.ready done"

verify.contract.compat: guard.prod.forbid
	@python3 scripts/verify/contract_compat_report.py

verify.platform.performance.smoke: guard.prod.forbid
	@python3 scripts/verify/platform_performance_smoke.py
	@python3 scripts/verify/product_hardening_schema_guard.py --report performance

.PHONY: verify.platform.performance.smoke.schema.guard
verify.platform.performance.smoke.schema.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/product_hardening_schema_guard.py
	@python3 scripts/verify/product_hardening_schema_guard.py --report performance

verify.platform.maturity.ready: guard.prod.forbid \
	verify.platform.distribution.ready \
	verify.contract.compat \
	verify.platform.performance.smoke \
	verify.platform.kernel.ready
	@echo "[OK] verify.platform.maturity.ready done"

verify.platform.reusability.ready: guard.prod.forbid \
	verify.owner.industry.isolation \
	verify.owner.intent.non_intrusion \
	verify.capability.isolation.report \
	verify.owner.scene.independent.deploy \
	verify.platform.kernel.ready
	@echo "[OK] verify.platform.reusability.ready done"

verify.platform.stability.ready: guard.prod.forbid \
	verify.platform.multi_domain.ready \
	verify.scene.conflict.stress \
	verify.capability.scale.stress \
	verify.intent.concurrent.smoke \
	verify.kernel.immutable.guard \
	verify.platform.reusability.ready
	@echo "[OK] verify.platform.stability.ready done"

verify.platform.governance.ready: guard.prod.forbid \
	verify.kernel.freeze.guard \
	verify.intent.public.surface.ready \
	verify.platform.sla.guard \
	verify.multi_tenant.evolution.smoke \
	verify.contract.version.evolution.drill \
	verify.platform.stability.ready
	@echo "[OK] verify.platform.governance.ready done"

verify.productization.ready: guard.prod.forbid \
	verify.docs.product_boundary \
	verify.user_module.product_boundary \
	verify.product.surface.clean \
	verify.product.bundle.isolation \
	verify.product.tier.enforcement \
	verify.ui.product.stability \
	verify.delivery.reproducible \
	verify.product.complexity.bound \
	verify.platform.governance.ready
	@echo "[OK] verify.productization.ready done"

verify.etag.validation.report: guard.prod.forbid
	@$(RUN_ENV) python3 scripts/verify/etag_validation_report.py

verify.auto_degrade.smoke.report: guard.prod.forbid
	@$(RUN_ENV) python3 scripts/verify/auto_degrade_smoke_report.py

verify.scene.drift.smoke.report: guard.prod.forbid
	@$(RUN_ENV) python3 scripts/verify/scene_drift_smoke_report.py

.PHONY: verify.scene.governance.smoke
verify.scene.governance.smoke: guard.prod.forbid
	@python3 scripts/verify/scene_governance_smoke.py

.PHONY: verify.intent.write.smoke
verify.intent.write.smoke: guard.prod.forbid
	@python3 scripts/verify/intent_write_smoke.py

.PHONY: verify.intent.write.runtime.smoke
verify.intent.write.runtime.smoke: guard.prod.forbid
	@python3 scripts/verify/intent_write_runtime_smoke.py

.PHONY: verify.intent.permission.matrix.report
verify.intent.permission.matrix.report: guard.prod.forbid
	@python3 scripts/verify/intent_permission_matrix_report.py

.PHONY: verify.intent.permission.matrix.guard
verify.intent.permission.matrix.guard: guard.prod.forbid verify.intent.permission.matrix.report
	@python3 scripts/verify/intent_permission_matrix_guard.py

.PHONY: verify.intent.write.sudo.guard
verify.intent.write.sudo.guard: guard.prod.forbid verify.intent.permission.matrix.report
	@python3 scripts/verify/write_intent_sudo_guard.py

verify.capability.orphan.report: guard.prod.forbid
	@$(RUN_ENV) python3 scripts/verify/capability_orphan_report.py

.PHONY: verify.platform.security.ready
verify.platform.security.ready: guard.prod.forbid \
	verify.system_group.business_acl.guard \
	verify.intent.write.guard \
	verify.intent.acl.mode \
	verify.intent.write.smoke \
	verify.intent.write.runtime.smoke \
	verify.intent.write.sudo.guard \
	verify.scene.governance.smoke \
	verify.intent.permission.matrix.guard
	@echo "[OK] verify.platform.security.ready done"

.PHONY: verify.system_group.business_acl.guard
verify.system_group.business_acl.guard: guard.prod.forbid
	@python3 scripts/verify/system_group_business_acl_guard.py

verify.platform.kernel.ready: guard.prod.forbid \
	verify.platform.security.ready \
	verify.scene.core_api_boundary.guard \
	verify.scene.provider.registry.guard \
	verify.scene.provider.registry.consumer.guard \
	verify.scene.provider_locator.removed.guard \
	verify.scene_orchestration.provider_shape.guard \
	verify.capability.provider.guard \
	verify.capability.registry.smoke \
	verify.contract.envelope \
	verify.write_intent.permission.audit \
	verify.auto_degrade.smoke.report \
	verify.scene.drift.smoke.report \
	verify.etag.validation.report \
	verify.intent.capability.matrix.report \
	verify.scene.intent.matrix.report \
	verify.intent.orphan.report \
	verify.capability.scene.matrix.report \
	verify.scene.intent.consistency \
	verify.intent.execution.path.report \
	verify.platform.kernel.baseline \
	verify.capability.orphan.report
	@echo "[OK] verify.platform.kernel.ready done"

verify.contract.snapshot: guard.prod.forbid verify.scene.contract.shape verify.contract.ordering.smoke verify.contract.catalog.determinism verify.system_init.snapshot_equivalence
	@echo "[OK] verify.contract.snapshot done"

verify.mode.filter: guard.prod.forbid verify.contract.mode.smoke verify.contract.api.mode.smoke
	@echo "[OK] verify.mode.filter done"

verify.capability.schema: guard.prod.forbid verify.scene_capability.contract.guard
	@echo "[OK] verify.capability.schema done"

verify.scene.schema: guard.prod.forbid verify.scene.definition.semantics verify.scene.catalog.source.guard verify.scene.contract.shape
	@echo "[OK] verify.scene.schema done"

verify.backend.architecture.full: guard.prod.forbid verify.intent.router.purity verify.baseline.policy_integrity.guard verify.smart_core.boundary_guard verify.app_config_engine.boundary_guard verify.boundary.guard verify.contract.envelope verify.mode.filter verify.capability.schema verify.scene.schema verify.seed.demo.isolation verify.scene.catalog.governance.guard verify.load_view.access.contract.guard verify.capability.provider.guard verify.capability.registry.smoke verify.release.capability.audit.schema.guard verify.phase_next.evidence.bundle verify.business.capability_baseline.guard verify.contract.snapshot verify.system_init.runtime_context.stability verify.contract.governance.coverage verify.contract.evidence.guard verify.scene.hud.trace.smoke verify.scene.meta.trace.smoke
	@if [ "$${SC_PHASE_NEXT_STRICT:-0}" = "1" ]; then \
	  $(MAKE) --no-print-directory verify.phase_next.evidence.bundle.strict; \
	else \
	  echo "[verify.backend.architecture.full] SC_PHASE_NEXT_STRICT=0: skip strict phase-next evidence bundle"; \
	fi
	@if [ "$${SC_BOUNDARY_IMPORT_STRICT:-0}" = "1" ]; then \
	  $(MAKE) --no-print-directory verify.boundary.import_guard.strict.guard; \
	else \
	  echo "[verify.backend.architecture.full] SC_BOUNDARY_IMPORT_STRICT=0: skip strict boundary import warning gate"; \
	fi
	@if [ "$${SC_RUNTIME_SURFACE_STRICT:-0}" = "1" ]; then \
	  $(MAKE) --no-print-directory verify.runtime.surface.dashboard.strict.guard; \
	else \
	  echo "[verify.backend.architecture.full] SC_RUNTIME_SURFACE_STRICT=0: skip strict runtime surface warning gate"; \
	fi
	@$(MAKE) --no-print-directory verify.backend.architecture.full.report.guard.schema.guard
	@$(MAKE) --no-print-directory verify.backend.evidence.manifest.guard
	@echo "[OK] verify.backend.architecture.full done"

verify.extension_modules.guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/extension_modules_guard.sh

verify.test_seed_dependency.guard: guard.prod.forbid
	@bash scripts/verify/test_seed_dependency_guard.sh

verify.contract_drift.guard: guard.prod.forbid
	@bash scripts/verify/contract_drift_guard.sh
	@$(MAKE) --no-print-directory verify.intent.side_effect_policy_guard

verify.intent.side_effect_policy_guard: guard.prod.forbid
	@python3 scripts/verify/side_effect_intent_policy_guard.py

verify.baseline.freeze_guard: guard.prod.forbid
	@python3 scripts/verify/baseline_freeze_guard.py

verify.business.increment.readiness: guard.prod.forbid
	@$(MAKE) --no-print-directory contract.catalog.export
	@$(MAKE) --no-print-directory verify.scene.contract.shape
	@$(MAKE) --no-print-directory audit.intent.surface
	@python3 scripts/verify/business_increment_readiness.py --profile $(BUSINESS_INCREMENT_PROFILE)

verify.business.increment.readiness.strict: guard.prod.forbid
	@$(MAKE) --no-print-directory contract.catalog.export
	@$(MAKE) --no-print-directory verify.scene.contract.shape
	@$(MAKE) --no-print-directory audit.intent.surface
	@python3 scripts/verify/business_increment_readiness.py --profile strict --strict

verify.business.increment.readiness.brief: guard.prod.forbid
	@$(MAKE) --no-print-directory verify.business.increment.readiness
	@python3 scripts/verify/business_increment_readiness_brief.py --profile $(BUSINESS_INCREMENT_PROFILE)

verify.business.increment.readiness.brief.strict: guard.prod.forbid
	@$(MAKE) --no-print-directory verify.business.increment.readiness.strict
	@python3 scripts/verify/business_increment_readiness_brief.py --profile strict --strict

verify.business.increment.preflight: guard.prod.forbid
	@$(MAKE) --no-print-directory contract.catalog.export
	@$(MAKE) --no-print-directory verify.scene.contract.shape
	@$(MAKE) --no-print-directory audit.intent.surface
	@$(MAKE) --no-print-directory verify.business.increment.readiness
	@echo "[OK] verify.business.increment.preflight done"

verify.business.increment.preflight.strict: guard.prod.forbid
	@$(MAKE) --no-print-directory verify.business.increment.preflight
	@$(MAKE) --no-print-directory verify.business.increment.readiness.strict
	@echo "[OK] verify.business.increment.preflight.strict done"

verify.docs.inventory: guard.prod.forbid
	@python3 scripts/verify/docs_inventory.py

verify.docs.links: guard.prod.forbid
	@python3 scripts/verify/docs_links.py

verify.docs.temp_guard: guard.prod.forbid
	@python3 scripts/verify/docs_temp_guard.py

verify.docs.contract_sync: guard.prod.forbid
	@python3 scripts/verify/docs_contract_sync.py

verify.docs.product_boundary: guard.prod.forbid
	@python3 scripts/verify/test_product_boundary_catalog_guard.py
	@python3 scripts/verify/product_boundary_catalog_guard.py

.PHONY: verify.industry_module.product_boundary
verify.industry_module.product_boundary: guard.prod.forbid
	@python3 -m py_compile scripts/verify/industry_module_product_boundary_guard.py
	@python3 scripts/verify/test_industry_module_product_boundary_guard.py
	@python3 scripts/verify/industry_module_product_boundary_guard.py

.PHONY: verify.user_module.product_boundary
verify.user_module.product_boundary: guard.prod.forbid
	@python3 -m py_compile scripts/verify/user_module_product_boundary_guard.py
	@python3 -m py_compile scripts/verify/user_module_data_rebaseline_contract_guard.py
	@python3 scripts/verify/user_module_product_boundary_guard.py
	@python3 scripts/verify/user_module_data_rebaseline_contract_guard.py

.PHONY: verify.user_module.data_baseline.runtime_audit
verify.user_module.data_baseline.runtime_audit: guard.prod.forbid check-compose-project check-compose-env verify.user_module.product_boundary
	@python3 -m py_compile scripts/verify/user_module_data_baseline_runtime_audit.py
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/user_module_data_baseline_runtime_audit.py

verify.docs.all: guard.prod.forbid verify.docs.inventory verify.docs.links verify.docs.temp_guard verify.docs.contract_sync verify.docs.product_boundary
	@echo "[OK] verify.docs.all done"

.PHONY: verify.portal.scene_product_filter_guard verify.portal.product_scene_mapping_guard verify.portal.role_home_scene_guard verify.portal.template_schema_guard verify.portal.entry_registry_guard verify.portal.entry_registry_quality_guard verify.portal.navigation_entry_registry_guard verify.portal.role_scene_navigation_guard verify.portal.navigation_registry_quality_guard
verify.portal.scene_product_filter_guard: guard.prod.forbid
	@python3 scripts/verify/portal_scene_product_filter_guard.py

verify.portal.product_scene_mapping_guard: guard.prod.forbid
	@python3 scripts/verify/portal_product_scene_mapping_guard.py

verify.portal.role_home_scene_guard: guard.prod.forbid
	@python3 scripts/verify/portal_role_home_scene_guard.py

verify.portal.template_schema_guard: guard.prod.forbid
	@python3 scripts/verify/portal_template_schema_guard.py

verify.portal.entry_registry_guard: guard.prod.forbid
	@python3 scripts/verify/portal_entry_registry_guard.py

verify.portal.entry_registry_quality_guard: guard.prod.forbid
	@python3 scripts/verify/portal_entry_registry_quality_guard.py

verify.portal.navigation_entry_registry_guard: guard.prod.forbid
	@python3 scripts/verify/portal_navigation_entry_registry_guard.py

verify.portal.role_scene_navigation_guard: guard.prod.forbid
	@python3 scripts/verify/portal_role_scene_navigation_guard.py

verify.portal.navigation_registry_quality_guard: guard.prod.forbid
	@python3 scripts/verify/portal_navigation_registry_quality_guard.py

verify.boundary.import_guard: guard.prod.forbid
	@python3 scripts/verify/boundary_import_guard.py
	@python3 scripts/verify/boundary_import_guard_schema_guard.py
	@python3 scripts/verify/model_ui_dependency_guard.py

verify.boundary.import_guard.schema.guard: guard.prod.forbid verify.boundary.import_guard
	@python3 scripts/verify/boundary_import_guard_schema_guard.py

verify.boundary.import_guard.strict.guard: guard.prod.forbid verify.boundary.import_guard.schema.guard
	@python3 scripts/verify/boundary_import_guard_strict_guard.py

verify.backend.boundary_guard: guard.prod.forbid
	@python3 scripts/verify/backend_boundary_guard.py

verify.scene.provider.guard: guard.prod.forbid
	@python3 scripts/verify/scene_provider_guard.py

verify.scene.core_api_boundary.guard: guard.prod.forbid
	@python3 scripts/verify/scene_core_api_boundary_guard.py

verify.scene.provider.registry.guard: guard.prod.forbid
	@python3 scripts/verify/scene_provider_registry_guard.py

verify.scene.provider.registry.consumer.guard: guard.prod.forbid
	@python3 scripts/verify/scene_provider_registry_consumer_guard.py

verify.scene.provider_locator.removed.guard: guard.prod.forbid
	@python3 scripts/verify/provider_locator_removed_guard.py

verify.scene_orchestration.provider_shape.guard: guard.prod.forbid
	@python3 scripts/verify/scene_orchestration_provider_shape_guard.py

.PHONY: verify.scene.provider_shape.guard
verify.scene.provider_shape.guard: guard.prod.forbid
	@$(MAKE) --no-print-directory verify.scene_orchestration.provider_shape.guard

.PHONY: verify.scene.contract_v1.field_schema.guard
verify.scene.contract_v1.field_schema.guard: guard.prod.forbid
	@python3 scripts/verify/scene_contract_v1_field_schema_guard.py

verify.capability.provider.guard: guard.prod.forbid
	@python3 scripts/verify/capability_provider_guard.py

verify.capability.registry.smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/capability_registry_smoke.py

verify.scene.hud.trace.smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/scene_hud_trace_smoke.py

verify.scene.meta.trace.smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/scene_meta_trace_smoke.py

verify.contract.governance.coverage: guard.prod.forbid
	@python3 scripts/verify/contract_governance_coverage.py

verify.scene_capability.contract.guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/scene_capability_contract_guard.py

verify.scene.capability.matrix.report: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/scene_capability_matrix_report.py

verify.scene.capability.matrix.schema.guard: guard.prod.forbid verify.scene.capability.matrix.report
	@python3 scripts/verify/scene_capability_matrix_report_schema_guard.py

verify.release.capability.audit: guard.prod.forbid check-compose-project check-compose-env verify.role.capability_floor.prod_like.schema.guard
	@$(RUN_ENV) python3 scripts/verify/release_capability_audit.py

verify.release.capability.audit.schema.guard: guard.prod.forbid verify.release.capability.audit
	@python3 scripts/verify/release_capability_audit_schema_guard.py

verify.contract.governance.brief: guard.prod.forbid
	@python3 scripts/verify/contract_governance_brief.py

verify.contract.scene_coverage.brief: guard.prod.forbid
	@python3 scripts/verify/scene_contract_coverage_brief.py

verify.contract.scene_coverage.guard: guard.prod.forbid verify.contract.scene_coverage.brief
	@python3 scripts/verify/scene_contract_coverage_schema_guard.py
	@python3 scripts/verify/scene_contract_coverage_baseline_guard.py

verify.contract.mode.smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/contract_mode_smoke.py

verify.contract.api.mode.smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/contract_api_mode_smoke.py

.PHONY: verify.contract.view_type_semantic.smoke verify.contract.view_type_semantic.strict.smoke
verify.contract.view_type_semantic.smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/contract_view_type_semantic_smoke.py

verify.contract.view_type_semantic.strict.smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) VIEW_TYPE_SMOKE_MIN_MODELS=2 python3 scripts/verify/contract_view_type_semantic_smoke.py

verify.round.v0_6.mini: guard.prod.forbid
	@$(MAKE) --no-print-directory verify.frontend.quick.gate
	@$(MAKE) --no-print-directory verify.portal.tree_view_smoke.container
	@BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 $(MAKE) --no-print-directory verify.contract.preflight
	@echo "[OK] verify.round.v0_6.mini done"

verify.contract.preflight: guard.prod.forbid
	@if [ "$(BASELINE_FREEZE_ENFORCE)" = "1" ]; then \
	  $(MAKE) --no-print-directory verify.baseline.freeze_guard; \
	else \
	  echo "[verify.contract.preflight] BASELINE_FREEZE_ENFORCE=0: skip baseline freeze guard"; \
	fi
	@$(MAKE) --no-print-directory verify.test_seed_dependency.guard
	@$(MAKE) --no-print-directory verify.contract_drift.guard
	@$(MAKE) --no-print-directory verify.scene.contract_path.gate
	@$(MAKE) --no-print-directory verify.contract.governance.coverage
	@$(MAKE) --no-print-directory verify.docs.all
	@$(MAKE) --no-print-directory verify.grouped.governance.bundle
	@$(MAKE) --no-print-directory audit.intent.surface INTENT_SURFACE_MD="$(CONTRACT_PREFLIGHT_INTENT_SURFACE_MD)" INTENT_SURFACE_JSON="$(CONTRACT_PREFLIGHT_INTENT_SURFACE_JSON)"
	@$(MAKE) --no-print-directory verify.scene_capability.contract.guard
	@$(MAKE) --no-print-directory verify.contract.governance.brief
	@$(MAKE) --no-print-directory verify.contract.scene_coverage.guard
	@$(MAKE) --no-print-directory verify.contract.mode.smoke
	@$(MAKE) --no-print-directory verify.project.form.contract.surface.guard
	@$(MAKE) --no-print-directory verify.relation.access_policy.consistency.audit
	@$(MAKE) --no-print-directory verify.system_group.business_acl.guard
	@$(MAKE) --no-print-directory verify.native_surface_integrity_guard
	@$(MAKE) --no-print-directory verify.governed_surface_policy_guard
	@$(MAKE) --no-print-directory verify.contract.surface_mapping_guard
	@$(MAKE) --no-print-directory verify.contract.parse_boundary.guard
	@$(MAKE) --no-print-directory verify.contract.production_chain.guard
	@$(MAKE) --no-print-directory verify.contract.ordering.smoke
	@$(MAKE) --no-print-directory verify.scene.hud.trace.smoke
	@$(MAKE) --no-print-directory verify.scene.meta.trace.smoke
	@$(MAKE) --no-print-directory verify.contract.api.mode.smoke
	@$(MAKE) --no-print-directory verify.contract.view_type_semantic.smoke
	@$(MAKE) --no-print-directory verify.frontend.search_groupby_savedfilters.guard
	@$(MAKE) --no-print-directory verify.frontend.x2many_command_semantic.guard
	@$(MAKE) --no-print-directory verify.frontend.view_type_render_coverage.guard
	@$(MAKE) --no-print-directory verify.native_view.semantic_page
	@if [ "$(CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES)" = "1" ]; then \
	  $(MAKE) --no-print-directory verify.contract.view_type_semantic.strict.smoke; \
	else \
	  echo "[verify.contract.preflight] CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0: skip strict view-type semantic smoke"; \
	fi
	@$(MAKE) --no-print-directory verify.scene.contract.shape
	@$(MAKE) --no-print-directory contract.evidence.export

.PHONY: verify.contract.preflight.resume
verify.contract.preflight.resume: guard.prod.forbid
	@BASELINE_FREEZE_ENFORCE="$(BASELINE_FREEZE_ENFORCE)" \
	CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES="$(CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES)" \
	CONTRACT_PREFLIGHT_INTENT_SURFACE_MD="$(CONTRACT_PREFLIGHT_INTENT_SURFACE_MD)" \
	CONTRACT_PREFLIGHT_INTENT_SURFACE_JSON="$(CONTRACT_PREFLIGHT_INTENT_SURFACE_JSON)" \
	bash scripts/verify/contract_preflight_resume.sh

audit.intent.surface: guard.prod.forbid
	@python3 scripts/audit/intent_surface_report.py --output-md "$(INTENT_SURFACE_MD)" --output-json "$(INTENT_SURFACE_JSON)"

policy.apply.extension_modules: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/apply_extension_modules.sh

policy.ensure.extension_modules: guard.prod.forbid check-compose-project check-compose-env
	@set -e; \
	if $(MAKE) --no-print-directory verify.extension_modules.guard DB_NAME=$(DB_NAME); then \
	  echo "[policy.ensure.extension_modules] already satisfied"; \
	elif [ "$${AUTO_FIX_EXTENSION_MODULES:-0}" = "1" ]; then \
	  echo "[policy.ensure.extension_modules] applying auto-fix"; \
	  $(MAKE) --no-print-directory policy.apply.extension_modules DB_NAME=$(DB_NAME); \
	  $(MAKE) --no-print-directory restart; \
	  $(MAKE) --no-print-directory verify.extension_modules.guard DB_NAME=$(DB_NAME); \
	else \
	  echo "[policy.ensure.extension_modules] FAIL: missing smart_construction_core in sc.core.extension_modules"; \
	  echo "[policy.ensure.extension_modules] HINT: re-run with AUTO_FIX_EXTENSION_MODULES=1 to auto-fix + restart"; \
	  exit 2; \
	fi

