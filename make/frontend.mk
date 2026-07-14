# ======================================================
# ==================== Frontend ========================
# ======================================================
.PHONY: fe.install fe.dev fe.gate verify.frontend.build prod.frontend.build verify.frontend.typecheck.strict verify.frontend.lint.src verify.frontend.quick.gate verify.frontend.relation_entry.contract_guard verify.frontend.relation_read_closure.guard verify.frontend.modifiers_runtime.guard verify.frontend.onchange_roundtrip.guard verify.frontend.onchange_contract_schema.guard verify.frontend.onchange_line_patch.guard verify.frontend.x2many_command_semantic.guard verify.frontend.x2many_inline_edit.guard verify.contract.subviews.guard verify.frontend.view_type_render_coverage.guard verify.frontend.view_type_contract_semantic.guard verify.frontend.search_groupby_savedfilters.guard verify.frontend.group_summary_runtime.guard verify.frontend.grouped_rows_runtime.guard verify.frontend.grouped_pagination_semantic.guard verify.frontend.grouped_pagination_semantic_drift.guard verify.contract.operation_gateway.guard verify.frontend.suggested_action.contract_guard verify.frontend.suggested_action.catalog verify.frontend.suggested_action.parser_guard verify.frontend.suggested_action.runtime_guard verify.frontend.suggested_action.import_boundary_guard verify.frontend.suggested_action.usage_guard verify.frontend.suggested_action.trace_export_guard verify.frontend.suggested_action.topk_guard verify.frontend.suggested_action.since_filter_guard verify.frontend.suggested_action.hud_export_guard verify.frontend.cross_stack_smoke verify.frontend.no_new_any_guard verify.frontend.suggested_action.all verify.portal.scene_observability.structure_guard verify.portal.scene_observability.structure_guard.update

fe.install:
	@scripts/dev/pnpm_exec.sh -C frontend install

fe.dev:
	@scripts/dev/pnpm_exec.sh -C frontend dev

fe.dev.reset: guard.prod.forbid
	@bash scripts/dev/frontend_dev_reset.sh

fe.dev.daily: guard.prod.forbid
	@FRONTEND_PROFILE=daily bash scripts/dev/frontend_dev_reset.sh

fe.dev.test: guard.prod.forbid
	@FRONTEND_PROFILE=test bash scripts/dev/frontend_dev_reset.sh

fe.dev.uat: guard.prod.forbid
	@FRONTEND_PROFILE=uat bash scripts/dev/frontend_dev_reset.sh

fe.gate:
	@scripts/dev/pnpm_exec.sh -C frontend gate

verify.frontend.build: guard.prod.forbid
	@bash scripts/dev/frontend_static_build.sh

prod.frontend.build: guard.prod.danger check-compose-project check-compose-env
	@bash scripts/dev/frontend_static_build.sh

verify.frontend.typecheck.strict: guard.prod.forbid
	@scripts/dev/pnpm_exec.sh -C frontend/apps/web typecheck:strict

verify.frontend.lint.src: guard.prod.forbid
	@scripts/dev/pnpm_exec.sh -C frontend/apps/web lint:src

.PHONY: verify.frontend.page_identity
verify.frontend.page_identity: guard.prod.forbid
	@node scripts/verify/frontend_page_identity_smoke.js
	@python3 scripts/verify/frontend_page_identity_guard.py

.PHONY: verify.frontend.style_system.guard
verify.frontend.style_system.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_style_system_guard.py

verify.frontend.relation_entry.contract_guard: guard.prod.forbid
	@python3 scripts/verify/relation_entry_contract_guard.py

verify.frontend.relation_read_closure.guard: guard.prod.forbid
	@python3 scripts/verify/relation_read_closure_guard.py

verify.frontend.modifiers_runtime.guard: guard.prod.forbid
	@python3 scripts/verify/modifiers_runtime_guard.py

verify.frontend.onchange_roundtrip.guard: guard.prod.forbid
	@python3 scripts/verify/onchange_roundtrip_guard.py

verify.frontend.onchange_contract_schema.guard: guard.prod.forbid
	@python3 scripts/verify/onchange_contract_schema_guard.py

verify.frontend.onchange_line_patch.guard: guard.prod.forbid
	@python3 scripts/verify/onchange_line_patch_guard.py

.PHONY: verify.scene.maturity.guard
verify.scene.maturity.guard: guard.prod.forbid
	@python3 scripts/verify/scene_maturity_guard.py

.PHONY: verify.scene.coverage.dashboard
verify.scene.coverage.dashboard: guard.prod.forbid
	@python3 scripts/verify/scene_coverage_dashboard_report.py

.PHONY: verify.scene.inventory.freeze.guard
verify.scene.inventory.freeze.guard: guard.prod.forbid
	@python3 scripts/verify/scene_inventory_freeze_guard.py

.PHONY: verify.scene.role.policy.consistency.guard
verify.scene.role.policy.consistency.guard: guard.prod.forbid
	@python3 scripts/verify/scene_role_policy_consistency_guard.py

.PHONY: verify.scene.data_source.schema.guard
verify.scene.data_source.schema.guard: guard.prod.forbid
	@python3 scripts/verify/scene_data_source_schema_guard.py

.PHONY: verify.scene.r3.runtime.guard
verify.scene.r3.runtime.guard: guard.prod.forbid
	@python3 scripts/verify/scene_r3_runtime_guard.py

.PHONY: verify.scene.r3.runtime.strict
verify.scene.r3.runtime.strict: guard.prod.forbid
	@python3 scripts/verify/scene_r3_runtime_guard.py \
		--max-action-chain-fail-count 0 \
		--min-pass-rate 1.0 \
		--min-action-chain-success-rate 0.50 \
		--max-action-chain-fallback-rate 0.50 \
		--fail-on-warning

.PHONY: gate.scene.r3.runtime.strict
gate.scene.r3.runtime.strict: verify.scene.r3.runtime.strict
	@echo "[gate.scene.r3.runtime.strict] PASS"

.PHONY: verify.scene.r3.runtime.quick
verify.scene.r3.runtime.quick: guard.prod.forbid gate.scene.r3.runtime.strict
	@echo "[verify.scene.r3.runtime.quick] summary"
	@sed -n '/^## Summary/,/^## Gate Thresholds/p' docs/ops/audit/scene_r3_runtime_dashboard.md | sed '$$d'
	@sed -n '/^## Gate Result/,/^## Checks/p' docs/ops/audit/scene_r3_runtime_dashboard.md | sed '$$d'

.PHONY: verify.scene.role.surface.consistency.guard
verify.scene.role.surface.consistency.guard: guard.prod.forbid
	@python3 scripts/verify/scene_role_surface_consistency_guard.py

.PHONY: verify.scene.inventory.draft.diff.report
verify.scene.inventory.draft.diff.report: guard.prod.forbid
	@python3 scripts/verify/scene_inventory_draft_diff_report.py

.PHONY: verify.scene.r1_r2.upgrade.queue.report
verify.scene.r1_r2.upgrade.queue.report: guard.prod.forbid
	@python3 scripts/verify/scene_r1_r2_upgrade_queue_report.py

.PHONY: verify.scene.r2_r3.upgrade.queue.report
verify.scene.r2_r3.upgrade.queue.report: guard.prod.forbid
	@python3 scripts/verify/scene_r2_r3_upgrade_queue_report.py

verify.frontend.x2many_command_semantic.guard: guard.prod.forbid
	@python3 scripts/verify/x2many_command_semantic_guard.py

verify.frontend.x2many_inline_edit.guard: guard.prod.forbid
	@python3 scripts/verify/x2many_inline_edit_guard.py

verify.contract.subviews.guard: guard.prod.forbid
	@python3 scripts/verify/subviews_contract_guard.py

verify.frontend.view_type_render_coverage.guard: guard.prod.forbid
	@python3 scripts/verify/view_type_render_coverage_guard.py

verify.frontend.view_type_contract_semantic.guard: guard.prod.forbid
	@python3 scripts/verify/view_type_contract_semantic_guard.py

.PHONY: verify.frontend.widget_richness.post_ga.guard
verify.frontend.widget_richness.post_ga.guard: guard.prod.forbid verify.frontend.x2many_command_semantic.guard verify.frontend.x2many_inline_edit.guard verify.contract.subviews.guard verify.frontend.view_type_render_coverage.guard verify.frontend.view_type_contract_semantic.guard verify.unified_page_contract.v2.web_consumer
	@echo "[OK] verify.frontend.widget_richness.post_ga.guard done"

verify.frontend.search_groupby_savedfilters.guard: guard.prod.forbid
	@python3 scripts/verify/search_groupby_savedfilters_guard.py

verify.frontend.group_summary_runtime.guard: guard.prod.forbid
	@python3 scripts/verify/group_summary_runtime_guard.py

verify.frontend.grouped_rows_runtime.guard: guard.prod.forbid
	@python3 scripts/verify/grouped_rows_runtime_guard.py

verify.payment_request_receipt_type.browser_group_smoke: guard.prod.forbid
	@node scripts/verify/payment_request_receipt_type_browser_group_smoke.js

verify.invoice_entry_fact.contract_guard: guard.prod.forbid
	@python3 scripts/verify/invoice_entry_fact_contract_guard.py

verify.invoice_entry_fact.runtime_smoke: guard.prod.forbid
	@node scripts/verify/invoice_entry_fact_runtime_smoke.js

verify.invoice_entry_fact.browser_smoke: guard.prod.forbid
	@node scripts/verify/invoice_entry_fact_browser_smoke.js

verify.frontend.grouped_pagination_semantic.guard: guard.prod.forbid
	@python3 scripts/verify/grouped_pagination_semantic_guard.py

verify.frontend.grouped_pagination_semantic_drift.guard: guard.prod.forbid
	@python3 scripts/verify/grouped_pagination_semantic_drift_guard.py

.PHONY: verify.frontend.grouped_contract_consistency.guard
verify.frontend.grouped_contract_consistency.guard: guard.prod.forbid
	@python3 scripts/verify/grouped_contract_consistency_guard.py

.PHONY: verify.frontend.grouped_drift_summary.guard
verify.frontend.grouped_drift_summary.guard: guard.prod.forbid
	@python3 scripts/verify/grouped_drift_summary_guard.py

.PHONY: verify.frontend.grouped_drift_summary.schema.guard
verify.frontend.grouped_drift_summary.schema.guard: guard.prod.forbid verify.frontend.grouped_drift_summary.guard
	@python3 scripts/verify/grouped_drift_summary_schema_guard.py

.PHONY: verify.frontend.grouped_drift_summary.baseline.guard
verify.frontend.grouped_drift_summary.baseline.guard: guard.prod.forbid verify.frontend.grouped_drift_summary.schema.guard
	@python3 scripts/verify/grouped_drift_summary_baseline_guard.py

.PHONY: verify.frontend.grouped_governance_brief.guard
verify.frontend.grouped_governance_brief.guard: guard.prod.forbid verify.frontend.grouped_drift_summary.baseline.guard verify.contract.governance.coverage
	@python3 scripts/verify/grouped_governance_brief_guard.py

.PHONY: verify.frontend.grouped_governance_brief.schema.guard
verify.frontend.grouped_governance_brief.schema.guard: guard.prod.forbid verify.frontend.grouped_governance_brief.guard
	@python3 scripts/verify/grouped_governance_brief_schema_guard.py

.PHONY: verify.frontend.grouped_governance_brief.baseline.guard
verify.frontend.grouped_governance_brief.baseline.guard: guard.prod.forbid verify.frontend.grouped_governance_brief.schema.guard
	@python3 scripts/verify/grouped_governance_brief_baseline_guard.py

.PHONY: verify.frontend.grouped_governance_policy_matrix
verify.frontend.grouped_governance_policy_matrix: guard.prod.forbid verify.frontend.grouped_governance_brief.baseline.guard
	@python3 scripts/verify/grouped_governance_policy_matrix.py

.PHONY: verify.frontend.grouped_governance_policy_matrix.schema.guard
verify.frontend.grouped_governance_policy_matrix.schema.guard: guard.prod.forbid verify.frontend.grouped_governance_policy_matrix
	@python3 scripts/verify/grouped_governance_policy_matrix_schema_guard.py

.PHONY: verify.frontend.grouped_governance_trend_consistency.guard
verify.frontend.grouped_governance_trend_consistency.guard: guard.prod.forbid verify.frontend.grouped_governance_policy_matrix.schema.guard
	@python3 scripts/verify/grouped_governance_trend_consistency_guard.py

.PHONY: verify.frontend.grouped_governance_trend_consistency.schema.guard
verify.frontend.grouped_governance_trend_consistency.schema.guard: guard.prod.forbid verify.frontend.grouped_governance_trend_consistency.guard
	@python3 scripts/verify/grouped_governance_trend_consistency_schema_guard.py

.PHONY: verify.frontend.grouped_governance_trend_consistency.baseline.guard
verify.frontend.grouped_governance_trend_consistency.baseline.guard: guard.prod.forbid verify.frontend.grouped_governance_trend_consistency.schema.guard
	@python3 scripts/verify/grouped_governance_trend_consistency_baseline_guard.py

.PHONY: verify.grouped.governance.bundle
verify.grouped.governance.bundle: guard.prod.forbid verify.frontend.grouped_rows_runtime.guard verify.frontend.grouped_pagination_semantic.guard verify.frontend.grouped_pagination_semantic_drift.guard verify.frontend.grouped_contract_consistency.guard verify.frontend.grouped_drift_summary.baseline.guard verify.frontend.grouped_governance_brief.baseline.guard verify.frontend.grouped_governance_policy_matrix.schema.guard verify.frontend.grouped_governance_trend_consistency.baseline.guard
	@python3 scripts/contract/export_evidence.py
	@python3 scripts/verify/contract_evidence_schema_guard.py
	@python3 scripts/verify/contract_evidence_guard.py
	@echo "[OK] verify.grouped.governance.bundle done"

verify.contract.operation_gateway.guard: guard.prod.forbid
	@python3 scripts/verify/operation_gateway_contract_guard.py

verify.frontend.quick.gate: guard.prod.forbid verify.frontend.page_identity verify.frontend.relation_entry.contract_guard verify.frontend.relation_read_closure.guard verify.frontend.modifiers_runtime.guard verify.frontend.onchange_roundtrip.guard verify.frontend.onchange_contract_schema.guard verify.frontend.onchange_line_patch.guard verify.frontend.x2many_command_semantic.guard verify.frontend.x2many_inline_edit.guard verify.contract.subviews.guard verify.frontend.view_type_render_coverage.guard verify.frontend.view_type_contract_semantic.guard verify.frontend.search_groupby_savedfilters.guard verify.frontend.group_summary_runtime.guard verify.frontend.grouped_rows_runtime.guard verify.frontend.grouped_pagination_semantic.guard verify.frontend.grouped_pagination_semantic_drift.guard verify.frontend.grouped_contract_consistency.guard verify.frontend.grouped_drift_summary.baseline.guard verify.frontend.typecheck.strict verify.frontend.build
	@echo "[OK] verify.frontend.quick.gate done"

verify.frontend.suggested_action.contract_guard: guard.prod.forbid
	@python3 scripts/verify/suggested_action_contract_guard.py

verify.frontend.suggested_action.catalog: guard.prod.forbid
	@python3 scripts/verify/suggested_action_catalog_export.py

verify.frontend.suggested_action.parser_guard: guard.prod.forbid
	@python3 scripts/verify/suggested_action_parser_guard.py

verify.frontend.suggested_action.runtime_guard: guard.prod.forbid
	@python3 scripts/verify/suggested_action_runtime_guard.py

verify.frontend.suggested_action.import_boundary_guard: guard.prod.forbid
	@python3 scripts/verify/suggested_action_import_boundary_guard.py

verify.frontend.suggested_action.usage_guard: guard.prod.forbid
	@python3 scripts/verify/suggested_action_usage_guard.py

verify.frontend.suggested_action.trace_export_guard: guard.prod.forbid
	@python3 scripts/verify/suggested_action_trace_export_guard.py

verify.frontend.suggested_action.topk_guard: guard.prod.forbid
	@python3 scripts/verify/suggested_action_topk_guard.py

verify.frontend.suggested_action.since_filter_guard: guard.prod.forbid
	@python3 scripts/verify/suggested_action_since_filter_guard.py

verify.frontend.suggested_action.hud_export_guard: guard.prod.forbid
	@python3 scripts/verify/suggested_action_hud_export_guard.py

verify.frontend.cross_stack_smoke: guard.prod.forbid
	@python3 scripts/verify/cross_stack_suggested_action_smoke.py

verify.frontend.no_new_any_guard: guard.prod.forbid
	@python3 scripts/verify/no_new_any_guard.py

verify.portal.scene_observability.structure_guard: guard.prod.forbid
	@python3 scripts/verify/scene_observability_structure_guard.py

verify.portal.scene_observability.structure_guard.update: guard.prod.forbid
	@python3 scripts/verify/scene_observability_structure_guard.py --update

verify.frontend.suggested_action.all: guard.prod.forbid verify.frontend.suggested_action.contract_guard verify.frontend.suggested_action.parser_guard verify.frontend.suggested_action.runtime_guard verify.frontend.suggested_action.import_boundary_guard verify.frontend.suggested_action.usage_guard verify.frontend.suggested_action.trace_export_guard verify.frontend.suggested_action.topk_guard verify.frontend.suggested_action.since_filter_guard verify.frontend.suggested_action.hud_export_guard verify.frontend.cross_stack_smoke verify.frontend.no_new_any_guard verify.frontend.suggested_action.catalog verify.frontend.typecheck.strict verify.frontend.build
	@echo "[OK] verify.frontend.suggested_action.all done"
