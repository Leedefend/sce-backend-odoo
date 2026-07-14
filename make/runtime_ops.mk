
# ==================== Diagnostics =====================
# ======================================================
.PHONY: diag.project odoo.shell.exec runtime.language.ensure verify.runtime.language.baseline verify.business.oca_runtime_smoke verify.business_config.guard_inventory verify.business_config.unit verify.business_config.coverage verify.business_config.snapshot verify.business_config.browser_acceptance verify.business_config.low_code_acceptance verify.business_config.config_workbench_operation_acceptance verify.business_config.low_code_runtime_consistency verify.business_config.low_code_group_matrix verify.business_config.low_code_layout_runtime verify.business_config.low_code_menu_navigation_alignment verify.business_config.low_code_global_stability verify.business_config.approval_runtime verify.business_config.full_acceptance verify.business.document_state_policy_switch verify.formal_entry_metadata.audit verify.user_role_approval_matrix.guard history.users.verify history.users.rebuild history.real_users.normalize.write history.user_data_migration.closure project.legacy_entry.backfill history.continuity.rehearse history.continuity.replay history.production.fresh_init history.business.usable.init history.business.usable.probe history.legacy_business_menu_exposure.close.write history.legacy_user_access.projection.write history.organization.department.materialize.write history.organization.carrying.audit.probe history.settlement_adjustment.runtime.probe history.expense_claim.runtime.probe history.treasury_reconciliation.runtime.probe history.receipt_income.runtime.probe history.payment_execution.runtime.probe history.construction_diary.runtime.probe history.attachment.custody.probe history.invoice_tax.runtime.probe history.treasury.reconciliation.probe history.expense_deposit.runtime.probe history.material_catalog.runtime.probe history.material_product.projection.probe history.purchase_contract.runtime.probe history.project.lifecycle.continuity.adapter migration.assets.fetch migration.assets.verify_all migration.assets.delivery_audit history.contract.core.gap.audit history.contract.partner.gap.audit history.contract.strong_evidence.backtrace.audit history.contract.direction_defer.audit history.partner.master.targeted.replay.adapter history.contract.partner.recovery.adapter history.contract.direction_defer.recovery.adapter history.partner.master.direction_defer.replay.adapter history.supplier.partner.targeted.replay.adapter history.outflow.partner.targeted.replay.adapter history.actual_outflow.partner.targeted.replay.adapter history.receipt.parent.recovery.adapter history.receipt.partner.targeted.replay.adapter history.receipt_income.partner.targeted.replay.adapter history.expense_deposit.partner.targeted.replay.adapter history.project_member.attachment.targeted.replay.adapter history.payment_request.outflow.state_activation.adapter history.payment_request.outflow.approved_recovery.adapter history.payment_request.outflow.done_recovery.adapter fresh_db.legacy_user_context.replay.adapter fresh_db.legacy_user_context.replay.write fresh_db.legacy_user_project_scope.replay.adapter fresh_db.legacy_task_evidence.replay.adapter fresh_db.legacy_attendance_checkin.replay.adapter fresh_db.legacy_personnel_movement.replay.adapter fresh_db.legacy_salary_line.replay.adapter fresh_db.legacy_purchase_contract.replay.adapter fresh_db.legacy_account_master.replay.adapter fresh_db.legacy_account_master.replay.write fresh_db.construction_contract.income_count_alignment.write fresh_db.construction_contract.income_count.probe fresh_db.construction_contract.visible_trace.write fresh_db.construction_contract.attachment.write fresh_db.construction_contract.attachment.probe fresh_db.construction_contract.replay_manifest.refresh fresh_db.fund_account.projection.write fresh_db.workbench_item.projection.write fresh_db.dashboard_cockpit.projection.write fresh_db.material_category.projection.write fresh_db.material_catalog.projection.write fresh_db.supplier_contract_pricing.projection.write prod.sim.partner.semantic.normalize.write prod.sim.formal.projections.refresh verify.prod.sim.formal.projections fresh_db.legacy_account_transaction.replay.adapter fresh_db.legacy_account_transaction.replay.write fresh_db.legacy_material_catalog.replay.adapter fresh_db.material_product.projection.write fresh_db.legacy_file_index.replay.adapter fresh_db.outflow_request.replay.adapter fresh_db.outflow_request.fact_coverage.write fresh_db.actual_outflow.replay.adapter fresh_db.actual_outflow_residual.replay.adapter fresh_db.actual_outflow_line.replay.adapter fresh_db.outflow_request_line.replay.adapter fresh_db.receipt_invoice_line.replay.adapter fresh_db.receipt_invoice_attachment.replay.adapter fresh_db.legacy_attachment_backfill.replay.adapter fresh_db.legacy_fund_daily_snapshot.replay.adapter fresh_db.legacy_fund_daily_line.replay.adapter fresh_db.legacy_financing_loan.replay.adapter fresh_db.legacy_receipt_income.replay.adapter fresh_db.legacy_expense_deposit.replay.adapter fresh_db.legacy_invoice_tax.replay.adapter fresh_db.legacy_tax_deduction.replay.adapter fresh_db.legacy_self_funding.replay.adapter fresh_db.legacy_invoice_registration_line.replay.adapter fresh_db.legacy_deduction_adjustment_line.replay.adapter fresh_db.legacy_fund_confirmation_line.replay.adapter fresh_db.legacy_expense_reimbursement_line.replay.adapter fresh_db.legacy_construction_diary_line.replay.adapter fresh_db.legacy_payment_residual.replay.adapter fresh_db.legacy_receipt_residual.replay.adapter fresh_db.legacy_workflow_audit.replay.adapter fresh_db.legacy_tax_deduction.replay.write fresh_db.legacy_self_funding.replay.write fresh_db.history_todo.projection.write fresh_db.treasury_ledger.projection.write fresh_db.settlement_adjustment.projection.write fresh_db.expense_claim.projection.write fresh_db.treasury_reconciliation.projection.write fresh_db.receipt_income.projection.write fresh_db.payment_execution.projection.write fresh_db.tax_deduction_registration.projection.write fresh_db.construction_diary.projection.write
.PHONY: verify.business_config.list_config_boundary verify.full_product_capability_scope verify.formal_business_operation_capability_matrix verify.formal_business_operation_core_flow_smoke verify.user_data.product_field_coverage.matrix verify.industry_module.handling_capability_boundary verify.user_formal_field.module_boundary.audit verify.formal_surface.transition_field_audit verify.core_history_field.physical_boundary_audit verify.formal_config.p1_alias_contract_audit verify.formal_config.p1_candidate_runtime_audit
.PHONY: verify.business.finance_document_tier_runtime_smoke verify.formal_business_backfill.audit verify.project_migration_field_continuity_gap.probe verify.construction_contract_history_value_gap.probe verify.visible_data_usability_warning.classify verify.tender_optional_scope_metadata.probe verify.platform_company_access_manifest.guard verify.platform_company_access_kernel.probe verify.business_scope.context.runtime verify.interfund_user_data.full_coverage.audit verify.interfund_borrow.classification_gap.audit verify.finance_interfund_category.handling_policy.audit verify.interfund_movement.fact.audit verify.interfund_movement_project.summary.audit verify.interfund_treasury_ledger.backfill_readiness.audit verify.company_contractor.responsibility_fact.audit verify.company_contractor.responsibility_summary.audit verify.finance_expense.approval_policy.audit verify.finance_business_fact.scope.audit verify.finance_business_fact.projection.audit verify.finance_business_project.summary.audit verify.finance_project_capital.position.audit verify.finance_project_counterparty.position.audit verify.finance_counterparty.position_summary.audit verify.finance_counterparty.identity_quality.audit verify.finance_position.drilldown_usability.audit verify.finance_interfund.projection.static_guard verify.finance_interfund.position.menu_runtime.audit verify.finance_interfund.position.bundle_summary verify.finance_interfund.position.all
.PHONY: fresh_db.deposit_claim.projection.write fresh_db.deposit_claim_taxonomy.projection.write fresh_db.repayment_registration.projection.write fresh_db.contractor_project_repay.projection.write fresh_db.project_repay_company.projection.write fresh_db.deduction_bill.projection.write fresh_db.deduction_paid.projection.write fresh_db.deduction_paid_refund.projection.write fresh_db.arrival_confirmation.projection.write fresh_db.fuel_card_operation.projection.write fresh_db.payment_execution_taxonomy.projection.write fresh_db.fund_account_between.projection.write fresh_db.fund_daily_report.projection.write project.cost.ledger.projection.write project.cost_ledger.projection.write
.PHONY: formal_entry_metadata.surface.write company_finance_expense.payment_execution.backfill.write direct_acceptance.construction_contract.income_execution.write joint_acceptance.contract.income_execution.write income_contract.settlement_surface.write direct_acceptance.engineering_settlement.income_projection.write verify.income_contract_execution.acceptance_projection verify.income_contract_settlement_surface.cutover verify.direct_acceptance_engineering_settlement.income_projection
.PHONY: history.legacy_user_visible_surface.overlay.write history.legacy_user_recovery.probe fresh_db.legacy_user_project_scope.replay.write
.PHONY: fresh_db.legacy_project_fund_balance.replay.adapter fresh_db.legacy_project_fund_balance.replay.write fresh_db.legacy_invoice_surcharge.replay.adapter fresh_db.legacy_invoice_surcharge.replay.write fresh_db.legacy_supplier_contract_pricing.replay.adapter fresh_db.legacy_supplier_contract_pricing.replay.write
diag.project: check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/diag/project.sh

odoo.shell.exec: check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh

runtime.language.ensure: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/ops/ensure_runtime_language_baseline.py

verify.runtime.language.baseline: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/runtime_language_baseline_probe.py

verify.business.oca_runtime_smoke: check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/business_oca_runtime_smoke.py

verify.business_config.guard_inventory: guard.prod.forbid
	@python3 -m py_compile scripts/verify/business_config_guard_inventory.py
	@python3 scripts/verify/business_config_guard_inventory.py

verify.business_config.unit: guard.prod.forbid verify.frontend.product_language.guard
	@python3 scripts/verify/business_config_user_language_guard.py
	@python3 scripts/verify/lowcode_config_boundary_guard.py
	@python3 scripts/verify/backend_contract_boundary_guard.py
	@python3 addons/smart_core/tests/test_backend_contract_boundaries.py
	@python3 addons/smart_core/tests/test_backend_contract_boundary_guard.py
	@python3 addons/smart_core/tests/test_business_config_contract_schema.py
	@python3 addons/smart_core/tests/test_api_data_write_id_boundaries.py
	@python3 addons/smart_core/tests/test_form_field_configuration_params.py
	@python3 addons/smart_core/tests/test_business_config_surface.py
	@python3 addons/smart_core/tests/test_menu_configuration_audit.py
	@python3 addons/smart_construction_core/tests/test_approval_policy_configuration_handler.py

verify.business_config.coverage: guard.prod.forbid check-compose-project check-compose-env
	@mkdir -p artifacts/backend
	@$(RUN_ENV) BUSINESS_CONFIG_COVERAGE_REPORT_PATH=/tmp/business_config_coverage_gate.json DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/business_config_coverage_gate.py
	@$(RUN_ENV) $(COMPOSE_BASE) cp $(ODOO_SERVICE):/tmp/business_config_coverage_gate.json artifacts/backend/business_config_coverage_gate.json >/dev/null

verify.business_config.list_config_boundary: guard.prod.forbid check-compose-project check-compose-env
	@mkdir -p artifacts/backend
	@$(RUN_ENV) BUSINESS_LIST_CONFIG_BOUNDARY_REPORT_PATH=/tmp/business_list_config_boundary_audit.json DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/business_list_config_boundary_audit.py
	@$(RUN_ENV) $(COMPOSE_BASE) cp $(ODOO_SERVICE):/tmp/business_list_config_boundary_audit.json artifacts/backend/business_list_config_boundary_audit.json >/dev/null

verify.full_product_capability_scope: guard.prod.forbid check-compose-project check-compose-env
	@mkdir -p artifacts/product docs/product
	@python3 -m py_compile scripts/verify/full_product_capability_scope_audit.py
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/full_product_capability_scope_audit.py
	@$(RUN_ENV) $(COMPOSE_BASE) cp $(ODOO_SERVICE):/tmp/sce-product-artifacts/full_product_capability_scope_v1.json artifacts/product/full_product_capability_scope_v1.json >/dev/null
	@$(RUN_ENV) $(COMPOSE_BASE) cp $(ODOO_SERVICE):/tmp/sce-product-artifacts/full_product_capability_scope_v1.md artifacts/product/full_product_capability_scope_v1.md >/dev/null
	@if [[ "$(UPDATE_PRODUCT_DOCS)" == "1" ]]; then \
	  $(RUN_ENV) $(COMPOSE_BASE) cp $(ODOO_SERVICE):/tmp/sce-product-artifacts/full_product_capability_scope_v1.md docs/product/full_product_capability_scope_v1.md >/dev/null; \
	fi

verify.formal_business_operation_capability_matrix: guard.prod.forbid check-compose-project check-compose-env
	@mkdir -p artifacts/product docs/product
	@python3 -m py_compile scripts/verify/formal_business_operation_capability_matrix.py
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/formal_business_operation_capability_matrix.py
	@$(RUN_ENV) $(COMPOSE_BASE) cp $(ODOO_SERVICE):/tmp/sce-product-artifacts/formal_business_operation_capability_matrix_v1.json artifacts/product/formal_business_operation_capability_matrix_v1.json >/dev/null
	@$(RUN_ENV) $(COMPOSE_BASE) cp $(ODOO_SERVICE):/tmp/sce-product-artifacts/formal_business_operation_capability_matrix_v1.md artifacts/product/formal_business_operation_capability_matrix_v1.md >/dev/null
	@if [[ "$(UPDATE_PRODUCT_DOCS)" == "1" ]]; then \
	  $(RUN_ENV) $(COMPOSE_BASE) cp $(ODOO_SERVICE):/tmp/sce-product-artifacts/formal_business_operation_capability_matrix_v1.md docs/product/formal_business_operation_capability_matrix_v1.md >/dev/null; \
	fi

verify.formal_business_operation_core_flow_smoke: guard.prod.forbid check-compose-project check-compose-env
	@mkdir -p artifacts/product docs/product
	@python3 -m py_compile scripts/verify/formal_business_operation_core_flow_smoke.py
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/formal_business_operation_core_flow_smoke.py
	@$(RUN_ENV) $(COMPOSE_BASE) cp $(ODOO_SERVICE):/tmp/sce-product-artifacts/formal_business_operation_core_flow_smoke_v1.json artifacts/product/formal_business_operation_core_flow_smoke_v1.json >/dev/null
	@$(RUN_ENV) $(COMPOSE_BASE) cp $(ODOO_SERVICE):/tmp/sce-product-artifacts/formal_business_operation_core_flow_smoke_v1.md artifacts/product/formal_business_operation_core_flow_smoke_v1.md >/dev/null
	@if [[ "$(UPDATE_PRODUCT_DOCS)" == "1" ]]; then \
	  $(RUN_ENV) $(COMPOSE_BASE) cp $(ODOO_SERVICE):/tmp/sce-product-artifacts/formal_business_operation_core_flow_smoke_v1.md docs/product/formal_business_operation_core_flow_smoke_v1.md >/dev/null; \
	fi

verify.user_data.product_field_coverage.matrix: guard.prod.forbid check-compose-project check-compose-env
	@mkdir -p artifacts/backend
	@python3 -m py_compile scripts/verify/user_data_product_field_coverage_matrix.py
	@$(RUN_ENV) USER_DATA_PRODUCT_FIELD_COVERAGE_MATRIX_PATH=/tmp/user_data_product_field_coverage_matrix.json DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/user_data_product_field_coverage_matrix.py
	@$(RUN_ENV) $(COMPOSE_BASE) cp $(ODOO_SERVICE):/tmp/user_data_product_field_coverage_matrix.json artifacts/backend/user_data_product_field_coverage_matrix.json >/dev/null

verify.industry_module.handling_capability_boundary: guard.prod.forbid check-compose-project check-compose-env
	@mkdir -p artifacts/backend
	@python3 -m py_compile scripts/verify/industry_module_handling_capability_boundary_audit.py
	@$(RUN_ENV) INDUSTRY_MODULE_HANDLING_CAPABILITY_BOUNDARY_AUDIT_PATH=/tmp/industry_module_handling_capability_boundary_audit.json DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/industry_module_handling_capability_boundary_audit.py
	@$(RUN_ENV) $(COMPOSE_BASE) cp $(ODOO_SERVICE):/tmp/industry_module_handling_capability_boundary_audit.json artifacts/backend/industry_module_handling_capability_boundary_audit.json >/dev/null

verify.user_formal_field.module_boundary.audit: guard.prod.forbid check-compose-project check-compose-env
	@python3 -m py_compile scripts/verify/user_formal_field_module_boundary_audit.py
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/user_formal_field_module_boundary_audit.py

verify.formal_surface.transition_field_audit: guard.prod.forbid
	@python3 -m py_compile scripts/verify/formal_surface_transition_field_audit.py
	@python3 scripts/verify/formal_surface_transition_field_audit.py

verify.core_history_field.physical_boundary_audit: guard.prod.forbid
	@python3 -m py_compile scripts/verify/core_history_field_physical_boundary_audit.py
	@python3 scripts/verify/core_history_field_physical_boundary_audit.py

verify.formal_config.p1_alias_contract_audit: guard.prod.forbid
	@python3 -m py_compile scripts/verify/formal_config_p1_alias_contract_audit.py
	@python3 scripts/verify/formal_config_p1_alias_contract_audit.py

verify.formal_config.p1_candidate_runtime_audit: guard.prod.forbid check-compose-project check-compose-env verify.formal_config.p1_alias_contract_audit
	@python3 -m py_compile scripts/verify/formal_config_p1_candidate_runtime_audit.py
	@$(RUN_ENV) $(COMPOSE_BASE) cp artifacts/backend/formal_config_p1_alias_contract_audit.json $(ODOO_SERVICE):/tmp/formal_config_p1_alias_contract_audit.json >/dev/null
	@$(RUN_ENV) $(COMPOSE_BASE) cp scripts/verify/baselines/formal_config_p1_candidate_runtime_budget_v1.json $(ODOO_SERVICE):/tmp/formal_config_p1_candidate_runtime_budget_v1.json >/dev/null
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/formal_config_p1_candidate_runtime_audit.py
	@$(RUN_ENV) $(COMPOSE_BASE) cp $(ODOO_SERVICE):/tmp/formal_config_p1_candidate_runtime_audit.json artifacts/backend/formal_config_p1_candidate_runtime_audit.json >/dev/null

verify.business_config.snapshot: guard.prod.forbid check-compose-project check-compose-env
	@mkdir -p artifacts/backend
	@$(RUN_ENV) BUSINESS_CONFIG_SNAPSHOT_PATH=/tmp/business_config_contract_snapshot.json BUSINESS_CONFIG_SNAPSHOT_COMPARE_PATH="$(BUSINESS_CONFIG_SNAPSHOT_COMPARE_PATH)" DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/business_config_contract_snapshot.py
	@$(RUN_ENV) $(COMPOSE_BASE) cp $(ODOO_SERVICE):/tmp/business_config_contract_snapshot.json artifacts/backend/business_config_contract_snapshot.json >/dev/null

verify.business_config.browser_acceptance: guard.prod.forbid
	@BASE_URL=$(WORKFLOW_CONTRACT_FRONTEND_URL) DB_NAME=$(DB_NAME) node scripts/verify/business_config_runtime_routes_browser_acceptance.mjs

verify.product.navigation_boundary: guard.prod.forbid
	@BASE_URL=$(WORKFLOW_CONTRACT_FRONTEND_URL) LOGIN=$${E2E_LOGIN:-admin} PASSWORD=$${E2E_PASSWORD:-admin} node frontend/apps/web/scripts/product_navigation_boundary_acceptance.mjs

.PHONY: verify.product.navigation_boundary

verify.business_config.low_code_acceptance: guard.prod.forbid
	@cd frontend/apps/web && BASE_URL=$(WORKFLOW_CONTRACT_FRONTEND_URL) DB_NAME=$(DB_NAME) E2E_LOGIN=$${E2E_LOGIN:-wutao} E2E_PASSWORD=$${E2E_PASSWORD:-123456} node scripts/low_code_business_config_acceptance.mjs

verify.business_config.config_workbench_operation_acceptance: guard.prod.forbid
	@cd frontend/apps/web && BASE_URL=$(WORKFLOW_CONTRACT_FRONTEND_URL) DB_NAME=$(DB_NAME) E2E_LOGIN=$${E2E_LOGIN:-wutao} E2E_PASSWORD=$${E2E_PASSWORD:-123456} node scripts/config_workbench_operation_acceptance.mjs

.PHONY: verify.business_config.config_workbench_operation_quick verify.business_config.config_workbench_operation_summary_guard verify.business_config.config_workbench_operation_local_closeout verify.product.page_structure

verify.business_config.config_workbench_operation_quick: guard.prod.forbid verify.frontend.product_language.guard
	@node --check frontend/apps/web/scripts/lib/product_page_structure_source.mjs
	@node --check frontend/apps/web/scripts/lib/config_workbench_operation_coverage.mjs
	@node --check frontend/apps/web/scripts/config_workbench_operation_coverage_guard.mjs
	@node --check frontend/apps/web/scripts/config_workbench_operation_acceptance.mjs
	@node --check frontend/apps/web/scripts/config_workbench_operation_summary_guard.mjs
	@node --check frontend/apps/web/scripts/product_page_structure_guard.mjs
	@node frontend/apps/web/scripts/config_workbench_operation_coverage_guard.mjs
	@$(MAKE) verify.product.page_structure
	@scripts/dev/pnpm_exec.sh -C frontend/apps/web typecheck
	@git diff --check

verify.product.page_structure: guard.prod.forbid
	@cd frontend/apps/web && node scripts/product_page_structure_guard.mjs

verify.business_config.config_workbench_operation_summary_guard: guard.prod.forbid
	@node frontend/apps/web/scripts/config_workbench_operation_summary_guard.mjs

verify.business_config.config_workbench_operation_local_closeout: guard.prod.forbid verify.business_config.config_workbench_operation_quick
	@ENV=$${ENV:-dev} DB_NAME=$(DB_NAME) FRONTEND_DIST_DIR=$${FRONTEND_DIST_DIR:-frontend/apps/web/dist-dev} bash scripts/dev/frontend_static_build.sh
	@container="$${FRONTEND_NGINX_CONTAINER:-$(COMPOSE_PROJECT_NAME)-nginx-1}"; \
	  if docker ps --format '{{.Names}}' | grep -qx "$$container"; then \
	    docker restart "$$container" >/dev/null; \
	    echo "[config-workbench.closeout] restarted $$container"; \
	  else \
	    echo "[config-workbench.closeout] nginx container not running: $$container" >&2; \
	    echo "Set FRONTEND_NGINX_CONTAINER or start the daily dev stack before local closeout." >&2; \
	    exit 2; \
	  fi
	@$(MAKE) DB_NAME=$(DB_NAME) WORKFLOW_CONTRACT_FRONTEND_URL=$(WORKFLOW_CONTRACT_FRONTEND_URL) verify.business_config.config_workbench_operation_acceptance
	@$(MAKE) verify.business_config.config_workbench_operation_summary_guard
	@scripts/dev/pnpm_exec.sh -C frontend/apps/web build
	@git diff --check

verify.business_config.low_code_runtime_consistency: guard.prod.forbid
	@cd frontend/apps/web && BASE_URL=$(WORKFLOW_CONTRACT_FRONTEND_URL) DB_NAME=$(DB_NAME) E2E_LOGIN=$${E2E_LOGIN:-wutao} E2E_PASSWORD=$${E2E_PASSWORD:-123456} node scripts/low_code_form_runtime_consistency_acceptance.mjs

verify.business_config.low_code_group_matrix: guard.prod.forbid
	@cd frontend/apps/web && BASE_URL=$(WORKFLOW_CONTRACT_FRONTEND_URL) DB_NAME=$(DB_NAME) E2E_LOGIN=$${E2E_LOGIN:-wutao} E2E_PASSWORD=$${E2E_PASSWORD:-123456} node scripts/low_code_form_group_matrix_acceptance.mjs

verify.business_config.low_code_layout_runtime: guard.prod.forbid
	@cd frontend/apps/web && BASE_URL=$(WORKFLOW_CONTRACT_FRONTEND_URL) DB_NAME=$(DB_NAME) E2E_LOGIN=$${E2E_LOGIN:-wutao} E2E_PASSWORD=$${E2E_PASSWORD:-123456} node scripts/low_code_form_layout_runtime_acceptance.mjs

verify.business_config.low_code_menu_navigation_alignment: guard.prod.forbid
	@cd frontend/apps/web && BASE_URL=$(WORKFLOW_CONTRACT_FRONTEND_URL) DB_NAME=$(DB_NAME) E2E_LOGIN=$${E2E_LOGIN:-wutao} E2E_PASSWORD=$${E2E_PASSWORD:-123456} node scripts/low_code_menu_navigation_alignment_acceptance.mjs

verify.business_config.low_code_global_stability: guard.prod.forbid
	@cd frontend/apps/web && BASE_URL=$(WORKFLOW_CONTRACT_FRONTEND_URL) DB_NAME=$(DB_NAME) E2E_LOGIN=$${E2E_LOGIN:-wutao} E2E_PASSWORD=$${E2E_PASSWORD:-123456} node scripts/low_code_global_stability_acceptance.mjs

verify.business_config.approval_runtime: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/business_config_approval_runtime_smoke.py

verify.business_config.full_acceptance: verify.business_config.guard_inventory verify.business_config.unit verify.frontend.build verify.business_config.coverage verify.business_config.list_config_boundary verify.full_product_capability_scope verify.business_config.snapshot verify.business_config.approval_runtime verify.business_config.browser_acceptance verify.product.navigation_boundary verify.business_config.low_code_acceptance verify.business_config.config_workbench_operation_acceptance verify.business_config.low_code_runtime_consistency verify.business_config.low_code_group_matrix verify.business_config.low_code_layout_runtime verify.business_config.low_code_menu_navigation_alignment verify.business_config.low_code_global_stability verify.user_menu.reachability.guard

verify.business.finance_document_tier_runtime_smoke: check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/business_finance_document_tier_runtime_smoke.py

verify.contract_product_menu.release: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/contract_product_menu_release_audit.py

verify.construction_product_menu.release: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/construction_product_menu_release_audit.py

.PHONY: policy.sync.config_center_menu_baseline
verify.production_menu.release_gate.guard.prod: guard.prod.readonly check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) PROD_READONLY_VERIFY=1 bash scripts/ops/odoo_shell_exec.sh < scripts/verify/production_menu_release_gate_guard.py

policy.sync.config_center_menu_baseline: guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) APPLY="$(APPLY)" DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/ops/config_center_menu_baseline_sync.py

policy.restore.formal_product_menu: guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/ops/formal_product_menu_policy_restore.py

verify.tender_optional_scope_metadata.probe: check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/tender_optional_scope_metadata_probe.py

verify.platform_company_access_manifest.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/platform_company_access_manifest_guard.py
	@python3 scripts/verify/platform_company_access_manifest_guard.py

verify.platform_company_access_kernel.probe: verify.platform_company_access_manifest.guard check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/platform_company_access_kernel_probe.py

verify.business_scope.context.runtime: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/business_scope_context_runtime_probe.py

verify.business.document_state_policy_switch: check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/business_document_state_policy_switch_smoke.py

verify.formal_entry_metadata.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/formal_entry_metadata_audit.py

verify.interfund_user_data.full_coverage.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/interfund_user_data_full_coverage_audit.py

verify.interfund_borrow.classification_gap.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/interfund_borrow_classification_gap_audit.py

verify.finance_interfund_category.handling_policy.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) scripts/ops/validate_finance_interfund_category_handling_policy.sh

verify.interfund_movement.fact.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/interfund_movement_fact_audit.py

verify.interfund_movement_project.summary.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/interfund_movement_project_summary_audit.py

verify.interfund_treasury_ledger.backfill_readiness.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) scripts/ops/validate_interfund_treasury_ledger_backfill_readiness.sh

verify.company_contractor.responsibility_fact.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/company_contractor_responsibility_fact_audit.py

verify.company_contractor.responsibility_summary.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/company_contractor_responsibility_summary_audit.py

verify.company_contractor.responsibility_http.smoke:
	@$(RUN_ENV) DB_NAME=$(DB_NAME) FRONTEND_URL="$${FRONTEND_URL:-http://127.0.0.1:18081}" E2E_LOGIN="$${E2E_LOGIN:-wutao}" E2E_PASSWORD="$${E2E_PASSWORD:-123456}" python3 scripts/verify/company_contractor_responsibility_http_smoke.py

verify.finance_handling.http_surface.smoke:
	@$(RUN_ENV) DB_NAME=$(DB_NAME) FRONTEND_URL="$${FRONTEND_URL:-http://127.0.0.1:18081}" E2E_LOGIN="$${E2E_LOGIN:-wutao}" E2E_PASSWORD="$${E2E_PASSWORD:-123456}" python3 scripts/verify/finance_handling_http_surface_smoke.py

verify.finance_legacy_cash_ledger.backfill_readiness.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) scripts/ops/validate_finance_legacy_cash_ledger_backfill_readiness.sh

verify.finance_expense_category.handling_policy.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) scripts/ops/validate_finance_expense_category_handling_policy.sh

verify.finance_expense.approval_policy.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) scripts/ops/validate_finance_expense_approval_policy.sh

verify.finance_legacy_cash_ledger.backfill.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) scripts/ops/validate_finance_legacy_cash_ledger_backfill.sh

backfill.finance_legacy_cash_ledger: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) APPLY=1 scripts/ops/validate_finance_legacy_cash_ledger_backfill.sh

verify.finance_legacy_source_less_ledger.reconciliation.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) scripts/ops/validate_finance_legacy_source_less_ledger_reconciliation.sh

verify.finance_legacy_source_less_ledger.attach.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) scripts/ops/validate_finance_legacy_source_less_ledger_attach.sh

backfill.finance_legacy_source_less_ledger.attach: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) APPLY=1 scripts/ops/validate_finance_legacy_source_less_ledger_attach.sh

verify.finance_legacy_source_linked_ledger.payment_request_boundary.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) scripts/ops/validate_finance_legacy_source_linked_ledger_payment_request_boundary.sh

backfill.finance_legacy_source_linked_ledger.payment_request_boundary: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) APPLY=1 scripts/ops/validate_finance_legacy_source_linked_ledger_payment_request_boundary.sh

verify.finance_legacy_handling.currency.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) scripts/ops/validate_finance_legacy_handling_currency.sh

backfill.finance_legacy_handling.currency: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) APPLY=1 scripts/ops/validate_finance_legacy_handling_currency.sh

verify.finance_legacy_treasury.currency.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) scripts/ops/validate_finance_legacy_treasury_currency.sh

backfill.finance_legacy_treasury.currency: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) APPLY=1 scripts/ops/validate_finance_legacy_treasury_currency.sh

verify.finance_p0.currency_default.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/finance_p0_currency_default_audit.py

verify.finance_business_fact.scope.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/finance_business_fact_scope_audit.py

verify.finance_business_fact.projection.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/finance_business_fact_projection_audit.py

verify.finance_business_project.summary.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/finance_business_project_summary_audit.py

verify.self_funding.handling.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/self_funding_handling_audit.py

verify.fund_daily.handling.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/fund_daily_handling_audit.py

verify.fund_account.balance_backfill_readiness.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/fund_account_balance_backfill_readiness_audit.py

backfill.fund_account.balance: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fund_account_balance_backfill_write.py

verify.finance_project_capital.position.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/finance_project_capital_position_audit.py

verify.finance_project_counterparty.position.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/finance_project_counterparty_position_audit.py

verify.finance_counterparty.position_summary.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/finance_counterparty_position_summary_audit.py

verify.finance_counterparty.identity_quality.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/finance_counterparty_identity_quality_audit.py

verify.finance_position.drilldown_usability.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/finance_position_drilldown_usability_audit.py

verify.finance_interfund.projection.static_guard: guard.prod.forbid
	@python3 scripts/verify/finance_interfund_projection_static_guard.py

verify.finance_interfund.position.menu_runtime.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/finance_interfund_position_menu_runtime_audit.py

verify.finance_interfund.position.bundle_summary: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/finance_interfund_position_bundle_summary.py

verify.finance_interfund.position.all: verify.finance_interfund.projection.static_guard verify.interfund_user_data.full_coverage.audit verify.interfund_borrow.classification_gap.audit verify.finance_business_fact.scope.audit verify.finance_business_fact.projection.audit verify.finance_business_project.summary.audit verify.interfund_movement.fact.audit verify.interfund_movement_project.summary.audit verify.interfund_treasury_ledger.backfill_readiness.audit verify.company_contractor.responsibility_fact.audit verify.company_contractor.responsibility_summary.audit verify.company_contractor.responsibility_http.smoke verify.finance_project_capital.position.audit verify.finance_project_counterparty.position.audit verify.finance_counterparty.position_summary.audit verify.finance_counterparty.identity_quality.audit verify.finance_position.drilldown_usability.audit verify.finance_interfund.position.menu_runtime.audit verify.finance_interfund.position.bundle_summary
	@echo "FINANCE_INTERFUND_POSITION_AUDIT_ALL_PASS db=$(DB_NAME)"

.PHONY: verify.business_capability.productization_p1 verify.business_system.usability_readiness verify.business_system.usability_readiness.prod verify.productization.system_closure.topic_guard verify.system_user_experience.coverage_guard verify.frontend.product_language.guard verify.frontend.config_workbench_navigation_boundary.guard verify.project_context.selector_product_boundary.guard verify.project_context.selector_product_boundary.guard.prod verify.formal_menu.no_legacy_carrier_guard verify.formal_menu.runtime_no_legacy_carrier_guard verify.formal_menu.runtime_no_legacy_carrier_guard.prod verify.formal_list_surface.no_test_placeholder_guard verify.formal_list_surface.no_test_placeholder_guard.prod policy.cleanup.formal_list_surface_test_contract verify.system_user_experience.quick verify.system_user_experience.shell_acceptance verify.system_user_experience.business_form_user_perspective verify.system_user_experience.visible_surface_visual_coverage verify.system_user_experience.full_browser verify.formal_business.release_gate formal_entry_metadata.non_business_creator.write
verify.formal_business.release_gate: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/validate_formal_business_release_gate.sh

verify.business_capability.productization_p1: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/validate_business_capability_productization_p1.sh

verify.business_system.usability_readiness: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" BUSINESS_SYSTEM_READINESS_INCLUDE_P1="$(BUSINESS_SYSTEM_READINESS_INCLUDE_P1)" BUSINESS_SYSTEM_READINESS_ARTIFACT_DIR="$(BUSINESS_SYSTEM_READINESS_ARTIFACT_DIR)" bash scripts/ops/validate_business_system_usability_readiness.sh

verify.business_system.usability_readiness.prod: guard.prod.readonly check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" BUSINESS_SYSTEM_READINESS_PROD_READONLY=1 BUSINESS_SYSTEM_READINESS_INCLUDE_P1=0 BUSINESS_SYSTEM_READINESS_ARTIFACT_DIR="$(BUSINESS_SYSTEM_READINESS_ARTIFACT_DIR)" bash scripts/ops/validate_business_system_usability_readiness.sh

verify.productization.system_closure.topic_guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/productization_system_closure_topic_guard.py scripts/verify/test_productization_system_closure_topic_guard.py
	@cd scripts/verify && python3 test_productization_system_closure_topic_guard.py
	@python3 scripts/verify/productization_system_closure_topic_guard.py

verify.system_user_experience.coverage_guard: guard.prod.forbid
	@python3 scripts/verify/system_user_experience_coverage_guard.py

verify.frontend.product_language.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/frontend_product_language_guard.py
	@python3 scripts/verify/frontend_product_language_guard.py

verify.frontend.config_workbench_navigation_boundary.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/frontend_config_workbench_navigation_boundary_guard.py
	@python3 scripts/verify/frontend_config_workbench_navigation_boundary_guard.py

verify.project_context.selector_product_boundary.guard: guard.prod.forbid check-compose-project check-compose-env
	@python3 -m py_compile scripts/verify/project_context_selector_product_boundary_guard.py
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/project_context_selector_product_boundary_guard.py

verify.project_context.selector_product_boundary.guard.prod: guard.prod.readonly check-compose-project check-compose-env
	@python3 -m py_compile scripts/verify/project_context_selector_product_boundary_guard.py
	@$(RUN_ENV) DB_NAME=$(DB_NAME) PROD_READONLY_VERIFY=1 bash scripts/ops/odoo_shell_exec.sh < scripts/verify/project_context_selector_product_boundary_guard.py

verify.formal_menu.no_legacy_carrier_guard:
	@python3 scripts/verify/formal_menu_no_legacy_carrier_guard.py

verify.formal_menu.runtime_no_legacy_carrier_guard: guard.prod.forbid check-compose-project check-compose-env verify.formal_menu.no_legacy_carrier_guard
	@python3 -m py_compile scripts/verify/formal_menu_runtime_no_legacy_carrier_guard.py
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/formal_menu_runtime_no_legacy_carrier_guard.py

verify.formal_menu.runtime_no_legacy_carrier_guard.prod: guard.prod.readonly check-compose-project check-compose-env verify.formal_menu.no_legacy_carrier_guard
	@python3 -m py_compile scripts/verify/formal_menu_runtime_no_legacy_carrier_guard.py
	@$(RUN_ENV) DB_NAME=$(DB_NAME) PROD_READONLY_VERIFY=1 bash scripts/ops/odoo_shell_exec.sh < scripts/verify/formal_menu_runtime_no_legacy_carrier_guard.py

verify.formal_list_surface.no_test_placeholder_guard: guard.prod.forbid check-compose-project check-compose-env
	@python3 -m py_compile scripts/verify/formal_list_surface_no_test_placeholder_guard.py
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/formal_list_surface_no_test_placeholder_guard.py

verify.formal_list_surface.no_test_placeholder_guard.prod: guard.prod.readonly check-compose-project check-compose-env
	@python3 -m py_compile scripts/verify/formal_list_surface_no_test_placeholder_guard.py
	@$(RUN_ENV) DB_NAME=$(DB_NAME) PROD_READONLY_VERIFY=1 bash scripts/ops/odoo_shell_exec.sh < scripts/verify/formal_list_surface_no_test_placeholder_guard.py

policy.cleanup.formal_list_surface_test_contract: guard.prod.danger check-compose-project check-compose-env
	@python3 -m py_compile scripts/ops/formal_list_surface_test_contract_cleanup.py
	@$(RUN_ENV) APPLY="$(APPLY)" DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/ops/formal_list_surface_test_contract_cleanup.py

verify.system_user_experience.quick: guard.prod.forbid verify.productization.system_closure.topic_guard verify.system_user_experience.coverage_guard verify.frontend.product_language.guard verify.frontend.config_workbench_navigation_boundary.guard verify.project_context.selector_product_boundary.guard verify.formal_menu.runtime_no_legacy_carrier_guard verify.formal_list_surface.no_test_placeholder_guard verify.product.page_structure
	@node --check frontend/apps/web/scripts/config_workbench_operation_acceptance.mjs
	@node --check frontend/apps/web/scripts/config_workbench_operation_summary_guard.mjs
	@node --check frontend/apps/web/scripts/business_form_user_perspective_acceptance.mjs
	@node --check frontend/apps/web/scripts/business_form_user_perspective_summary_guard.mjs
	@node --check frontend/apps/web/scripts/system_user_experience_shell_acceptance.mjs
	@node --check frontend/apps/web/scripts/system_user_experience_shell_summary_guard.mjs
	@node --check frontend/apps/web/scripts/user_page_visual_coverage.cjs
	@node --check frontend/apps/web/scripts/user_visible_surface_visual_coverage_summary_guard.mjs
	@node --check frontend/apps/web/scripts/system_user_experience_full_browser_summary_guard.mjs
	@git diff --check

verify.system_user_experience.shell_acceptance: guard.prod.forbid
	@cd frontend/apps/web && BASE_URL=$(WORKFLOW_CONTRACT_FRONTEND_URL) DB_NAME=$(DB_NAME) E2E_LOGIN=$${E2E_LOGIN:-wutao} E2E_PASSWORD=$${E2E_PASSWORD:-123456} node scripts/system_user_experience_shell_acceptance.mjs
	@cd frontend/apps/web && node scripts/system_user_experience_shell_summary_guard.mjs

verify.system_user_experience.business_form_user_perspective: guard.prod.forbid
	@BASE_URL=$(WORKFLOW_CONTRACT_FRONTEND_URL) DB_NAME=$(DB_NAME) E2E_LOGIN=$${E2E_LOGIN:-wutao} E2E_PASSWORD=$${E2E_PASSWORD:-123456} node frontend/apps/web/scripts/business_form_user_perspective_acceptance.mjs
	@cd frontend/apps/web && node scripts/business_form_user_perspective_summary_guard.mjs

verify.system_user_experience.visible_surface_visual_coverage: guard.prod.forbid
	@BASE_URL=$(WORKFLOW_CONTRACT_FRONTEND_URL) DB=$(DB_NAME) LOGIN=$${E2E_LOGIN:-wutao} PASSWORD=$${E2E_PASSWORD:-123456} SKIP_FORMS=1 node frontend/apps/web/scripts/user_page_visual_coverage.cjs
	@cd frontend/apps/web && node scripts/user_visible_surface_visual_coverage_summary_guard.mjs

verify.system_user_experience.full_browser: guard.prod.forbid verify.system_user_experience.coverage_guard verify.product.page_structure verify.business_config.config_workbench_operation_acceptance verify.business_config.config_workbench_operation_summary_guard verify.system_user_experience.shell_acceptance verify.system_user_experience.visible_surface_visual_coverage verify.system_user_experience.business_form_user_perspective
	@cd frontend/apps/web && node scripts/system_user_experience_full_browser_summary_guard.mjs
	@echo "[OK] verify.system_user_experience.full_browser done"

formal_entry_metadata.surface.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) FORMAL_ENTRY_METADATA_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/ops/formal_entry_metadata_surface_write.py

formal_entry_metadata.non_business_creator.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) FORMAL_ENTRY_METADATA_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/ops/formal_entry_metadata_non_business_creator_write.py

company_finance_expense.payment_execution.backfill.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/company_finance_expense_payment_execution_backfill_write.py

direct_acceptance.construction_contract.income_execution.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/direct_acceptance_construction_contract_income_execution_write.py

joint_acceptance.contract.income_execution.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/joint_acceptance_contract_income_execution_write.py

income_contract.settlement_surface.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/income_contract_settlement_surface_write.py

direct_acceptance.engineering_settlement.income_projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/direct_acceptance_engineering_settlement_income_projection_write.py

verify.income_contract_execution.acceptance_projection: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/income_contract_execution_acceptance_projection_audit.py

verify.income_contract_settlement_surface.cutover: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/income_contract_settlement_surface_cutover_audit.py

verify.direct_acceptance_engineering_settlement.income_projection: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/direct_acceptance_engineering_settlement_income_projection_audit.py

verify.user_role_approval_matrix.guard: check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/user_role_approval_matrix_guard.py

.PHONY: verify.user_permission_view_contract_boundary.guard
verify.user_permission_view_contract_boundary.guard: check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/user_permission_view_contract_boundary_guard.py

.PHONY: verify.form_structure.contract.guard verify.form_structure.contract_runtime.audit verify.form_structure.contract verify.form_view.native_structure.boundary_guard verify.smart_core.boundary_guard verify.view.orchestration_boundary_guard verify.view.orchestration_product_boundary_guard verify.app_config_engine.boundary_guard verify.view.orchestration_user_surface.browser verify.form_view.orchestration_boundary_guard verify.form_view.scope.boundary_guard verify.user_form.preference.boundary_guard verify.user_form.preference.runtime_audit verify.user_menu.preference.runtime_audit verify.user_menu.reachability.guard verify.industry_form.required_marker_audit verify.industry_list.delete_action_audit verify.application_form.required_marker_audit verify.business_form.productization.standard.guard verify.business_form.productization.audit verify.payment_execution.form_productization.runtime_guard verify.form_view.scope.runtime_chain_guard verify.form_view.scope.action_projection_audit verify.action_default_group.contract_audit
verify.smart_core.boundary_guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/smart_core_boundary_guard.py
	@python3 scripts/verify/smart_core_boundary_guard.py

verify.view.orchestration_product_boundary_guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/view_orchestration_product_boundary_guard.py
	@python3 scripts/verify/view_orchestration_product_boundary_guard.py

verify.app_config_engine.boundary_guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/app_config_engine_boundary_guard.py
	@python3 scripts/verify/app_config_engine_boundary_guard.py

verify.form_view.scope.boundary_guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/form_view_scope_boundary_guard.py
	@python3 scripts/verify/form_view_scope_boundary_guard.py

verify.user_form.preference.boundary_guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/user_form_preference_boundary_guard.py
	@python3 scripts/verify/user_form_preference_boundary_guard.py

verify.user_form.preference.runtime_audit: guard.prod.forbid check-compose-project check-compose-env verify.user_form.preference.boundary_guard
	@python3 -m py_compile scripts/verify/user_form_preference_runtime_audit.py
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/user_form_preference_runtime_audit.py

verify.user_menu.preference.runtime_audit: guard.prod.forbid check-compose-project check-compose-env
	@python3 -m py_compile scripts/verify/user_menu_preference_runtime_audit.py
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/user_menu_preference_runtime_audit.py

verify.user_menu.reachability.guard: guard.prod.forbid check-compose-project check-compose-env
	@python3 -m py_compile scripts/verify/user_menu_reachability_guard.py
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/user_menu_reachability_guard.py

verify.industry_form.required_marker_audit: guard.prod.forbid check-compose-project check-compose-env
	@python3 -m py_compile scripts/verify/industry_form_required_marker_audit.py
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/industry_form_required_marker_audit.py

verify.industry_list.delete_action_audit: guard.prod.forbid check-compose-project check-compose-env
	@python3 -m py_compile scripts/verify/industry_list_delete_action_audit.py
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/industry_list_delete_action_audit.py

verify.application_form.required_marker_audit: guard.prod.forbid check-compose-project check-compose-env
	@python3 -m py_compile scripts/verify/application_form_required_marker_audit.py
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/application_form_required_marker_audit.py

verify.business_form.productization.standard.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/business_form_productization_standard_guard.py
	@python3 scripts/verify/business_form_productization_standard_guard.py

verify.business_form.productization.audit: guard.prod.forbid verify.business_form.productization.standard.guard verify.smart_core.boundary_guard verify.view.orchestration_product_boundary_guard verify.app_config_engine.boundary_guard
	@python3 -m py_compile scripts/verify/business_form_productization_audit.py
	@python3 scripts/verify/business_form_productization_audit.py

verify.payment_execution.form_productization.runtime_guard: guard.prod.forbid check-compose-project check-compose-env
	@python3 -m py_compile scripts/verify/payment_execution_form_productization_runtime_guard.py
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/payment_execution_form_productization_runtime_guard.py

verify.form_view.scope.runtime_chain_guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/form_view_scope_runtime_chain_guard.py
	@python3 scripts/verify/form_view_scope_runtime_chain_guard.py

verify.form_view.scope.action_projection_audit: guard.prod.forbid check-compose-project check-compose-env
	@python3 -m py_compile scripts/verify/form_view_scope_action_projection_audit.py
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/form_view_scope_action_projection_audit.sh

verify.action_default_group.contract_audit: guard.prod.forbid check-compose-project check-compose-env
	@python3 -m py_compile scripts/verify/action_default_group_contract_audit.py
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/action_default_group_contract_audit.py

verify.form_view.native_structure.boundary_guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/form_view_native_structure_boundary_guard.py
	@python3 scripts/verify/form_view_native_structure_boundary_guard.py

verify.view.orchestration_boundary_guard: guard.prod.forbid
	@python3 -m py_compile addons/smart_core/core/view_orchestration_contract.py addons/smart_core/core/view_orchestrator.py addons/smart_core/model/ui_business_config_contract.py scripts/verify/view_orchestration_boundary_guard.py
	@python3 scripts/verify/view_orchestration_boundary_guard.py

verify.view.orchestration_user_surface.browser: guard.prod.forbid check-compose-project check-compose-env
	@FRONTEND_URL=$${FRONTEND_URL:-http://127.0.0.1:5174} DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) node scripts/verify/view_orchestration_user_surface_browser_acceptance.js

verify.form_view.orchestration_boundary_guard: verify.view.orchestration_boundary_guard

verify.form_structure.contract.guard: guard.prod.forbid
	@python3 -m py_compile addons/smart_core/core/unified_page_contract_v2_assembler.py scripts/verify/form_structure_contract_standardizer_guard.py scripts/verify/form_structure_contract_runtime_audit.py
	@python3 scripts/verify/form_structure_contract_standardizer_guard.py

verify.form_structure.contract_runtime.audit: guard.prod.forbid check-compose-project check-compose-env verify.form_structure.contract.guard verify.form_view.native_structure.boundary_guard verify.view.orchestration_boundary_guard verify.form_view.scope.boundary_guard verify.user_form.preference.runtime_audit verify.form_view.scope.runtime_chain_guard verify.form_view.scope.action_projection_audit
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/form_structure_contract_runtime_audit.sh

verify.form_structure.contract: verify.form_view.scope.boundary_guard verify.user_form.preference.boundary_guard verify.user_form.preference.runtime_audit verify.form_view.scope.runtime_chain_guard verify.form_view.scope.action_projection_audit verify.form_view.native_structure.boundary_guard verify.view.orchestration_boundary_guard verify.form_structure.contract_runtime.audit
	@echo "[OK] verify.form_structure.contract done"

history.users.verify: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/user_asset_verify.py --asset-root "$(MIGRATION_ASSET_ROOT)" --lane user --check

history.users.rebuild: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/migration/user_history_rebuild.sh

history.real_users.normalize.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/history_real_user_normalize_write.py

history.user_data_migration.closure: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) python3 scripts/verify/user_data_migration_closure_gate.py

project.legacy_entry.backfill: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) PROJECT_LEGACY_ENTRY_BACKFILL_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/ops/project_legacy_entry_backfill.py

history.legacy_user_visible_surface.overlay.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" LEGACY_USER_VISIBLE_SURFACE_FILES="$(LEGACY_USER_VISIBLE_SURFACE_FILES)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/legacy_user_visible_surface_overlay_write.py

history.daily_business_visible_surface.p0.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/daily_business_visible_surface_p0_plan_write.py

history.daily_business_visible_surface.p0.probe: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/daily_business_visible_surface_p0_plan_probe.py

history.daily_business_visible_surface.p0.runtime_gap.probe: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/daily_business_visible_surface_p0_runtime_gap_probe.py

history.daily_business_visible_surface.p0.runtime_gap.write: guard.prod.forbid check-compose-project check-compose-env history.daily_business_visible_surface.p0.runtime_gap.probe
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/daily_business_visible_surface_p0_runtime_gap_write.py

history.daily_business_visible_surface.p0: history.daily_business_visible_surface.p0.write history.daily_business_visible_surface.p0.probe history.daily_business_visible_surface.p0.runtime_gap.write
	@echo "[OK] history.daily_business_visible_surface.p0 done"

history.user_profile_runtime_projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/history_user_profile_runtime_projection_write.py

history.legacy_user_recovery.probe: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/history_legacy_user_recovery_probe.py

.PHONY: project.master.user_review.decision_template project.master.user_review.decision_validate project.master.user_review.decision_apply.dry_run project.master.user_review.decision_apply user.acceptance.project_master.materialize.dry_run user.acceptance.project_master.materialize
project.master.user_review.decision_template: guard.prod.forbid
	@python3 scripts/migration/user_project_master_review_decision_template.py --input-dir "$${PROJECT_MASTER_REVIEW_INPUT_DIR:-/tmp/project_master_stabilization_host}" --out "$${PROJECT_MASTER_REVIEW_DECISION_CSV:-artifacts/project_master_stabilization/user_project_master_review_decisions_20260520.csv}"

project.master.user_review.decision_validate: guard.prod.forbid
	@python3 scripts/migration/user_project_master_review_decision_template.py --validate-decisions "$${PROJECT_MASTER_REVIEW_DECISION_CSV:-artifacts/project_master_stabilization/user_project_master_review_decisions_20260520.csv}" --summary-json "$${PROJECT_MASTER_REVIEW_DECISION_RESULT:-artifacts/project_master_stabilization/user_project_master_review_decisions_20260520_validate.json}"

project.master.user_review.decision_apply.dry_run: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" PROJECT_MASTER_REVIEW_DECISION_CSV="$${PROJECT_MASTER_REVIEW_DECISION_CSV:-migration_assets/10_master/project/user_project_master_review_decisions_20260521.csv}" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/user_project_master_decision_apply.py

project.master.user_review.decision_apply: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" PROJECT_MASTER_REVIEW_DECISION_CSV="$${PROJECT_MASTER_REVIEW_DECISION_CSV:-migration_assets/10_master/project/user_project_master_review_decisions_20260521.csv}" APPLY=1 bash scripts/ops/odoo_shell_exec.sh < scripts/migration/user_project_master_decision_apply.py

user.acceptance.project_master.materialize.dry_run: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/migration/user_acceptance_project_master_materialize.py

user.acceptance.project_master.materialize: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) APPLY=1 bash scripts/ops/odoo_shell_exec.sh < scripts/migration/user_acceptance_project_master_materialize.py

fresh_db.legacy_user_context.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_user_context_replay_adapter.py

fresh_db.legacy_user_context.replay.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_legacy_user_context_replay_write.py

history.organization.department.materialize.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/history_organization_department_materialize_write.py

history.organization.carrying.audit.probe: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/history_organization_carrying_audit_probe.py

fresh_db.legacy_user_project_scope.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_user_project_scope_replay_adapter.py

fresh_db.legacy_user_project_scope.replay.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_legacy_user_project_scope_replay_write.py

fresh_db.legacy_task_evidence.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_task_evidence_replay_adapter.py

fresh_db.legacy_attendance_checkin.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_attendance_checkin_replay_adapter.py

fresh_db.legacy_personnel_movement.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_personnel_movement_replay_adapter.py

fresh_db.legacy_salary_line.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_salary_line_replay_adapter.py

fresh_db.legacy_purchase_contract.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_purchase_contract_replay_adapter.py

fresh_db.legacy_invoice_registration_line.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_invoice_registration_line_replay_adapter.py

fresh_db.legacy_deduction_adjustment_line.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_deduction_adjustment_line_replay_adapter.py

fresh_db.legacy_fund_confirmation_line.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_fund_confirmation_line_replay_adapter.py

fresh_db.legacy_expense_reimbursement_line.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_expense_reimbursement_line_replay_adapter.py

fresh_db.legacy_construction_diary_line.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_construction_diary_line_replay_adapter.py

fresh_db.legacy_payment_residual.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_payment_residual_replay_adapter.py

fresh_db.legacy_receipt_residual.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_receipt_residual_replay_adapter.py

fresh_db.legacy_material_catalog.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_material_catalog_replay_adapter.py

fresh_db.material_product.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" MIGRATION_MATERIAL_PRODUCT_LIMIT="$(MIGRATION_MATERIAL_PRODUCT_LIMIT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_material_product_projection_write.py

fresh_db.legacy_account_master.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_account_master_replay_adapter.py

fresh_db.legacy_account_master.replay.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_legacy_account_master_replay_write.py

.PHONY: fresh_db.construction_contract.new_xlsx_income.write fresh_db.construction_contract.income_fact_stub.write
fresh_db.construction_contract.income_count_alignment.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_construction_contract_income_count_alignment_write.py

fresh_db.construction_contract.new_xlsx_income.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" CONSTRUCTION_CONTRACT_NEW_XLSX="$(CONSTRUCTION_CONTRACT_NEW_XLSX)" CONSTRUCTION_CONTRACT_NEW_XLSX_JSON="$(CONSTRUCTION_CONTRACT_NEW_XLSX_JSON)" CONSTRUCTION_CONTRACT_NEW_XLSX_EXPECTED_ROWS="$(CONSTRUCTION_CONTRACT_NEW_XLSX_EXPECTED_ROWS)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_new_construction_contract_xlsx_income_write.py

fresh_db.construction_contract.income_fact_stub.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_income_fact_project_stub_write.py

fresh_db.construction_contract.income_count.probe: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_construction_contract_income_count_probe.py

fresh_db.construction_contract.visible_trace.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" MIGRATION_FILE_INDEX_CSV="$(MIGRATION_FILE_INDEX_CSV)" CONSTRUCTION_CONTRACT_VISIBLE_XLSX="$(CONSTRUCTION_CONTRACT_VISIBLE_XLSX)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_construction_contract_visible_trace_write.py

fresh_db.construction_contract.attachment.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" MIGRATION_FILE_INDEX_CSV="$(MIGRATION_FILE_INDEX_CSV)" CONSTRUCTION_CONTRACT_RAW_CSV="$(CONSTRUCTION_CONTRACT_RAW_CSV)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_construction_contract_attachment_write.py

fresh_db.construction_contract.attachment.probe: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" MIGRATION_FILE_INDEX_CSV="$(MIGRATION_FILE_INDEX_CSV)" CONSTRUCTION_CONTRACT_RAW_CSV="$(CONSTRUCTION_CONTRACT_RAW_CSV)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_construction_contract_attachment_probe.py

fresh_db.construction_contract.replay_manifest.refresh: guard.prod.forbid
	@python3 scripts/migration/fresh_db_construction_contract_replay_manifest_refresh.py

.PHONY: project.positive_migration.reconcile.probe project.positive_migration.visibility.refresh.write
project.positive_migration.reconcile.probe: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" PROJECT_POSITIVE_MIGRATION_EXCEL_PATH="$(PROJECT_POSITIVE_MIGRATION_EXCEL_PATH)" PROJECT_POSITIVE_MIGRATION_RAW_CONTRACT_CSV="$(PROJECT_POSITIVE_MIGRATION_RAW_CONTRACT_CSV)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/project_contract_fact_alias_reconciliation.py

project.positive_migration.visibility.refresh.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(or $(MIGRATION_REPLAY_DB_ALLOWLIST),$(DB_NAME))" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" PROJECT_POSITIVE_MIGRATION_EXCEL_PATH="$(PROJECT_POSITIVE_MIGRATION_EXCEL_PATH)" PROJECT_POSITIVE_MIGRATION_RAW_CONTRACT_CSV="$(PROJECT_POSITIVE_MIGRATION_RAW_CONTRACT_CSV)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/project_positive_migration_visibility_refresh_write.py

fresh_db.fund_account.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_fund_account_projection_write.py

fresh_db.workbench_item.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_workbench_item_projection_write.py

fresh_db.dashboard_cockpit.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_dashboard_cockpit_projection_write.py

fresh_db.material_category.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_material_category_projection_write.py

fresh_db.material_catalog.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_material_catalog_projection_write.py

fresh_db.supplier_contract_pricing.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_supplier_contract_pricing_projection_write.py

project.cost_ledger.projection.write: project.cost.ledger.projection.write

project.cost.ledger.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(or $(MIGRATION_REPLAY_DB_ALLOWLIST),$(DB_NAME))" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/project_cost_ledger_projection_write.py

fresh_db.tax_deduction_registration.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_tax_deduction_registration_projection_write.py

prod.sim.partner.semantic.normalize.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/prod_sim_partner_semantic_normalize_write.py

prod.sim.formal.projections.refresh: guard.prod.forbid check-compose-project check-compose-env
	@$(MAKE) prod.sim.business.usable.init

verify.prod.sim.formal.projections: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(FORMAL_PROJECTION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/formal_projection_refresh_probe.py

verify.formal_business_backfill.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/formal_business_backfill_audit_probe.py

verify.project_migration_field_continuity_gap.probe: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/project_migration_field_continuity_gap_probe.py

verify.construction_contract_history_value_gap.probe: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" CONSTRUCTION_CONTRACT_RAW_CSV="$(CONSTRUCTION_CONTRACT_RAW_CSV)" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/construction_contract_history_value_gap_probe.py

verify.visible_data_usability_warning.classify: guard.prod.forbid
	@$(RUN_ENV) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" SYSTEMIC_FIELD_GAP_ARTIFACT_BASE="$(SYSTEMIC_FIELD_GAP_ARTIFACT_BASE)" python3 scripts/verify/visible_data_usability_warning_classification.py

fresh_db.legacy_account_transaction.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_account_transaction_replay_adapter.py

fresh_db.legacy_account_transaction.replay.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_legacy_account_transaction_replay_write.py

fresh_db.legacy_file_index.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_file_index_replay_adapter.py

.PHONY: verify.legacy_attachment.mirror.completeness.audit
verify.legacy_attachment.mirror.completeness.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) LEGACY_ATTACHMENT_COMPLETENESS_SOURCE_CONTAINS="$${LEGACY_ATTACHMENT_COMPLETENESS_SOURCE_CONTAINS:-$(ATTACHMENT_AUDIT_SOURCE_CONTAINS)}" LEGACY_ATTACHMENT_COMPLETENESS_STRICT="$${LEGACY_ATTACHMENT_COMPLETENESS_STRICT:-$(ATTACHMENT_AUDIT_STRICT)}" LEGACY_ATTACHMENT_COMPLETENESS_ALLOW_MISSING_FILES="$${LEGACY_ATTACHMENT_COMPLETENESS_ALLOW_MISSING_FILES:-$(ATTACHMENT_AUDIT_ALLOW_MISSING_FILES)}" LEGACY_ATTACHMENT_COMPLETENESS_LIMIT="$${LEGACY_ATTACHMENT_COMPLETENESS_LIMIT:-$(ATTACHMENT_AUDIT_LIMIT)}" LEGACY_ATTACHMENT_COMPLETENESS_PRINT_FULL="$${LEGACY_ATTACHMENT_COMPLETENESS_PRINT_FULL:-$(ATTACHMENT_AUDIT_PRINT_FULL)}" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/legacy_attachment_mirror_completeness_audit.py

.PHONY: verify.legacy_attachment.mirror.completeness.audit.prod
verify.legacy_attachment.mirror.completeness.audit.prod: guard.prod.readonly check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) LEGACY_ATTACHMENT_COMPLETENESS_SOURCE_CONTAINS="$${LEGACY_ATTACHMENT_COMPLETENESS_SOURCE_CONTAINS:-$(ATTACHMENT_AUDIT_SOURCE_CONTAINS)}" LEGACY_ATTACHMENT_COMPLETENESS_STRICT=1 LEGACY_ATTACHMENT_COMPLETENESS_ALLOW_MISSING_FILES="$${LEGACY_ATTACHMENT_COMPLETENESS_ALLOW_MISSING_FILES:-$(or $(ATTACHMENT_AUDIT_ALLOW_MISSING_FILES),0)}" LEGACY_ATTACHMENT_COMPLETENESS_LIMIT="$${LEGACY_ATTACHMENT_COMPLETENESS_LIMIT:-$(or $(ATTACHMENT_AUDIT_LIMIT),0)}" LEGACY_ATTACHMENT_COMPLETENESS_PRINT_FULL="$${LEGACY_ATTACHMENT_COMPLETENESS_PRINT_FULL:-$(ATTACHMENT_AUDIT_PRINT_FULL)}" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/legacy_attachment_mirror_completeness_audit.py

.PHONY: verify.legacy_online_attachment.mirror.job.audit
verify.legacy_online_attachment.mirror.job.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) LEGACY_ATTACHMENT_JOB_ROOT="$${LEGACY_ATTACHMENT_JOB_ROOT:-$(ATTACHMENT_JOB_AUDIT_JOB_ROOT)}" LEGACY_ATTACHMENT_JOB_AUDIT_SOURCE_CONTAINS="$${LEGACY_ATTACHMENT_JOB_AUDIT_SOURCE_CONTAINS:-$(ATTACHMENT_JOB_AUDIT_SOURCE_CONTAINS)}" LEGACY_ATTACHMENT_JOB_AUDIT_STRICT="$${LEGACY_ATTACHMENT_JOB_AUDIT_STRICT:-$(ATTACHMENT_JOB_AUDIT_STRICT)}" LEGACY_ATTACHMENT_JOB_AUDIT_ALLOW_JOB_FAILURES="$${LEGACY_ATTACHMENT_JOB_AUDIT_ALLOW_JOB_FAILURES:-$(ATTACHMENT_JOB_AUDIT_ALLOW_JOB_FAILURES)}" LEGACY_ATTACHMENT_JOB_AUDIT_ALLOW_MISSING_FILES="$${LEGACY_ATTACHMENT_JOB_AUDIT_ALLOW_MISSING_FILES:-$(ATTACHMENT_JOB_AUDIT_ALLOW_MISSING_FILES)}" LEGACY_ATTACHMENT_JOB_AUDIT_INDEX_LIMIT="$${LEGACY_ATTACHMENT_JOB_AUDIT_INDEX_LIMIT:-$(ATTACHMENT_JOB_AUDIT_INDEX_LIMIT)}" LEGACY_ATTACHMENT_JOB_AUDIT_PRINT_FULL="$${LEGACY_ATTACHMENT_JOB_AUDIT_PRINT_FULL:-$(ATTACHMENT_JOB_AUDIT_PRINT_FULL)}" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/legacy_online_attachment_mirror_job_audit.py

.PHONY: verify.legacy_online_attachment.custody.evidence
verify.legacy_online_attachment.custody.evidence: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) LEGACY_ATTACHMENT_CUSTODY_EVIDENCE_JOB_ROOT="$${LEGACY_ATTACHMENT_CUSTODY_EVIDENCE_JOB_ROOT:-$(ATTACHMENT_JOB_AUDIT_JOB_ROOT)}" LEGACY_ATTACHMENT_CUSTODY_EVIDENCE_SOURCE_CONTAINS="$${LEGACY_ATTACHMENT_CUSTODY_EVIDENCE_SOURCE_CONTAINS:-$(or $(ATTACHMENT_JOB_AUDIT_SOURCE_CONTAINS),online_old)}" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/legacy_online_attachment_custody_evidence.py

.PHONY: verify.legacy_online_attachment.custody.evidence.prod
verify.legacy_online_attachment.custody.evidence.prod: guard.prod.readonly check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) LEGACY_ATTACHMENT_CUSTODY_EVIDENCE_JOB_ROOT="$${LEGACY_ATTACHMENT_CUSTODY_EVIDENCE_JOB_ROOT:-$(ATTACHMENT_JOB_AUDIT_JOB_ROOT)}" LEGACY_ATTACHMENT_CUSTODY_EVIDENCE_SOURCE_CONTAINS="$${LEGACY_ATTACHMENT_CUSTODY_EVIDENCE_SOURCE_CONTAINS:-$(or $(ATTACHMENT_JOB_AUDIT_SOURCE_CONTAINS),online_old)}" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/legacy_online_attachment_custody_evidence.py

.PHONY: verify.legacy_online_attachment.mirror.job.audit.prod
verify.legacy_online_attachment.mirror.job.audit.prod: guard.prod.readonly check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) LEGACY_ATTACHMENT_JOB_ROOT="$${LEGACY_ATTACHMENT_JOB_ROOT:-$(ATTACHMENT_JOB_AUDIT_JOB_ROOT)}" LEGACY_ATTACHMENT_JOB_AUDIT_SOURCE_CONTAINS="$${LEGACY_ATTACHMENT_JOB_AUDIT_SOURCE_CONTAINS:-$(or $(ATTACHMENT_JOB_AUDIT_SOURCE_CONTAINS),online_old)}" LEGACY_ATTACHMENT_JOB_AUDIT_STRICT=1 LEGACY_ATTACHMENT_JOB_AUDIT_ALLOW_JOB_FAILURES="$${LEGACY_ATTACHMENT_JOB_AUDIT_ALLOW_JOB_FAILURES:-$(or $(ATTACHMENT_JOB_AUDIT_ALLOW_JOB_FAILURES),0)}" LEGACY_ATTACHMENT_JOB_AUDIT_ALLOW_MISSING_FILES="$${LEGACY_ATTACHMENT_JOB_AUDIT_ALLOW_MISSING_FILES:-$(or $(ATTACHMENT_JOB_AUDIT_ALLOW_MISSING_FILES),0)}" LEGACY_ATTACHMENT_JOB_AUDIT_INDEX_LIMIT="$${LEGACY_ATTACHMENT_JOB_AUDIT_INDEX_LIMIT:-$(or $(ATTACHMENT_JOB_AUDIT_INDEX_LIMIT),0)}" LEGACY_ATTACHMENT_JOB_AUDIT_PRINT_FULL="$${LEGACY_ATTACHMENT_JOB_AUDIT_PRINT_FULL:-$(ATTACHMENT_JOB_AUDIT_PRINT_FULL)}" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/legacy_online_attachment_mirror_job_audit.py

.PHONY: verify.legacy_attachment.missing_residual.summarize
verify.legacy_attachment.missing_residual.summarize:
	@python3 scripts/verify/legacy_attachment_missing_residual_summarize.py --input "$(ATTACHMENT_MISSING_RESIDUAL_INPUT)" --output "$(ATTACHMENT_MISSING_RESIDUAL_OUTPUT)"

.PHONY: verify.legacy_attachment.frontend_browser.acceptance.host
verify.legacy_attachment.frontend_browser.acceptance.host:
	@FRONTEND_URL="$(LEGACY_ATTACHMENT_BROWSER_FRONTEND_URL)" DB_NAME="$(DB_NAME)" LEGACY_ATTACHMENT_BROWSER_SAMPLES='$(LEGACY_ATTACHMENT_BROWSER_SAMPLES)' LEGACY_ATTACHMENT_BROWSER_SAMPLES_FILE="$(LEGACY_ATTACHMENT_BROWSER_SAMPLES_FILE)" node scripts/verify/legacy_attachment_frontend_browser_acceptance.js

.PHONY: verify.attachment_upload.frontend_browser.acceptance.host
verify.attachment_upload.frontend_browser.acceptance.host:
	@FRONTEND_URL="$(LEGACY_ATTACHMENT_BROWSER_FRONTEND_URL)" DB_NAME="$(DB_NAME)" E2E_LOGIN="$(E2E_LOGIN)" E2E_PASSWORD="$(E2E_PASSWORD)" MVP_MODEL="$(MVP_MODEL)" RECORD_ID="$(RECORD_ID)" ACTION_ID="$(ACTION_ID)" MENU_ID="$(MENU_ID)" node scripts/verify/attachment_upload_frontend_browser_acceptance.js

.PHONY: verify.attachment_upload.frontend_browser.matrix.host
verify.attachment_upload.frontend_browser.matrix.host:
	@FRONTEND_URL="$(LEGACY_ATTACHMENT_BROWSER_FRONTEND_URL)" DB_NAME="$(DB_NAME)" E2E_LOGIN="$(E2E_LOGIN)" E2E_PASSWORD="$(E2E_PASSWORD)" ATTACHMENT_UPLOAD_BROWSER_SAMPLES_FILE="$(ATTACHMENT_UPLOAD_BROWSER_SAMPLES_FILE)" ATTACHMENT_UPLOAD_BROWSER_LIMIT="$(ATTACHMENT_UPLOAD_BROWSER_LIMIT)" node scripts/verify/attachment_upload_frontend_browser_matrix_acceptance.js

.PHONY: verify.attachment_upload.surface_manifest.prod
verify.attachment_upload.surface_manifest.prod: guard.prod.readonly check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) LEGACY_ATTACHMENT_UPLOAD_SURFACE_LOGIN="$${ATTACHMENT_UPLOAD_SURFACE_LOGIN:-$(E2E_LOGIN)}" LEGACY_ATTACHMENT_UPLOAD_SURFACE_OUTPUT="$(ATTACHMENT_UPLOAD_SURFACE_MANIFEST_OUTPUT)" LEGACY_ATTACHMENT_UPLOAD_SURFACE_REQUIRED_MODELS="$(ATTACHMENT_UPLOAD_SURFACE_REQUIRED_MODELS)" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/attachment_upload_surface_manifest.py

.PHONY: verify.legacy_attachment.frontend_browser.sample_manifest.prod
verify.legacy_attachment.frontend_browser.sample_manifest.prod: guard.prod.readonly check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) LEGACY_ATTACHMENT_BROWSER_SAMPLE_MANIFEST_OUTPUT="$(LEGACY_ATTACHMENT_BROWSER_SAMPLE_MANIFEST_OUTPUT)" LEGACY_ATTACHMENT_BROWSER_SAMPLE_PER_MIMETYPE="$(LEGACY_ATTACHMENT_BROWSER_SAMPLE_PER_MIMETYPE)" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/legacy_attachment_frontend_browser_sample_manifest.py

.PHONY: legacy_attachment.custody_marker.backfill
legacy_attachment.custody_marker.backfill: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) LEGACY_ATTACHMENT_CUSTODY_MARKER_APPLY="$${LEGACY_ATTACHMENT_CUSTODY_MARKER_APPLY:-1}" LEGACY_ATTACHMENT_CUSTODY_MARKER_LIMIT="$${LEGACY_ATTACHMENT_CUSTODY_MARKER_LIMIT:-0}" LEGACY_ATTACHMENT_CUSTODY_MARKER_OUTPUT="$${LEGACY_ATTACHMENT_CUSTODY_MARKER_OUTPUT:-/tmp/legacy_attachment_custody_marker_backfill_result_v1.json}" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/legacy_attachment_custody_marker_backfill.py

.PHONY: legacy_attachment.custody_marker.backfill.prod
legacy_attachment.custody_marker.backfill.prod: guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) LEGACY_ATTACHMENT_CUSTODY_MARKER_APPLY="$${LEGACY_ATTACHMENT_CUSTODY_MARKER_APPLY:-1}" LEGACY_ATTACHMENT_CUSTODY_MARKER_LIMIT="$${LEGACY_ATTACHMENT_CUSTODY_MARKER_LIMIT:-0}" LEGACY_ATTACHMENT_CUSTODY_MARKER_OUTPUT="$${LEGACY_ATTACHMENT_CUSTODY_MARKER_OUTPUT:-/tmp/legacy_attachment_custody_marker_backfill_result_v1.json}" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/legacy_attachment_custody_marker_backfill.py

history.continuity.rehearse: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) HISTORY_CONTINUITY_MODE=rehearse RUN_ID="$(RUN_ID)" HISTORY_CONTINUITY_START_AT="$(HISTORY_CONTINUITY_START_AT)" HISTORY_CONTINUITY_STOP_AFTER="$(HISTORY_CONTINUITY_STOP_AFTER)" MIGRATION_REPLAY_DB_ALLOWLIST="$(or $(MIGRATION_REPLAY_DB_ALLOWLIST),$(DB_NAME))" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/migration/history_continuity_oneclick.sh

history.continuity.replay: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) HISTORY_CONTINUITY_MODE=replay HISTORY_CONTINUITY_INCLUDE_FORMAL_PROJECTIONS=0 RUN_ID="$(RUN_ID)" HISTORY_CONTINUITY_START_AT="$(HISTORY_CONTINUITY_START_AT)" HISTORY_CONTINUITY_STOP_AFTER="$(HISTORY_CONTINUITY_STOP_AFTER)" MIGRATION_REPLAY_DB_ALLOWLIST="$(or $(MIGRATION_REPLAY_DB_ALLOWLIST),$(DB_NAME))" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/migration/history_continuity_oneclick.sh

history.production.fresh_init: guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) RUN_ID="$(RUN_ID)" HISTORY_CONTINUITY_START_AT="$(HISTORY_CONTINUITY_START_AT)" HISTORY_CONTINUITY_STOP_AFTER="$(HISTORY_CONTINUITY_STOP_AFTER)" MIGRATION_REPLAY_DB_ALLOWLIST="$(or $(MIGRATION_REPLAY_DB_ALLOWLIST),$(DB_NAME))" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/deploy/fresh_production_history_init.sh

history.business.usable.init: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) FORMAL_PROJECTION_ARTIFACT_ROOT="$(FORMAL_PROJECTION_ARTIFACT_ROOT)" MIGRATION_REPLAY_DB_ALLOWLIST="$(or $(MIGRATION_REPLAY_DB_ALLOWLIST),$(DB_NAME))" bash scripts/migration/history_business_usable_init.sh

history.business.usable.probe: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/history_business_usable_probe.py

history.legacy_business_menu_exposure.close.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(or $(MIGRATION_REPLAY_DB_ALLOWLIST),$(DB_NAME))" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/history_legacy_business_menu_exposure_close_write.py

verify.user_visible_business_fact_alignment: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/user_visible_business_fact_alignment_probe.py

.PHONY: verify.business_user_priority_menu_plan.alignment
verify.business_user_priority_menu_plan.alignment: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/business_user_priority_menu_plan_probe.py

.PHONY: migration.scbs_55_user_visible_surface.live_alignment.write
migration.scbs_55_user_visible_surface.live_alignment.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(or $(MIGRATION_REPLAY_DB_ALLOWLIST),$(DB_NAME))" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/scbs_55_user_visible_surface_live_alignment_write.py

.PHONY: migration.scbs_55_user_visible_surface.target_carrier.write
migration.scbs_55_user_visible_surface.target_carrier.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(or $(MIGRATION_REPLAY_DB_ALLOWLIST),$(DB_NAME))" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/scbs_55_user_visible_surface_target_carrier_write.py

.PHONY: migration.scbs_55_user_visible_surface.target_view.write
migration.scbs_55_user_visible_surface.target_view.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(or $(MIGRATION_REPLAY_DB_ALLOWLIST),$(DB_NAME))" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/scbs_55_user_visible_surface_target_view_write.py

.PHONY: verify.scbs_55_user_visible_surface.custom_gap.audit
verify.scbs_55_user_visible_surface.custom_gap.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/scbs_55_user_visible_surface_custom_gap_probe.py

.PHONY: migration.scbs_55_user_visible_surface.custom_gap.status.write
migration.scbs_55_user_visible_surface.custom_gap.status.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(or $(MIGRATION_REPLAY_DB_ALLOWLIST),$(DB_NAME))" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/scbs_55_user_visible_surface_custom_gap_status_write.py

.PHONY: migration.scbs_55_user_visible_surface.dashboard_contract.write
migration.scbs_55_user_visible_surface.dashboard_contract.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(or $(MIGRATION_REPLAY_DB_ALLOWLIST),$(DB_NAME))" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/scbs_55_user_visible_surface_dashboard_contract_write.py

.PHONY: verify.user_priority.browser_evidence.coverage
verify.user_priority.browser_evidence.coverage: guard.prod.forbid
	@python3 scripts/verify/user_priority_browser_evidence_coverage.py

.PHONY: verify.user_priority.page_alignment.complete
verify.user_priority.page_alignment.complete: guard.prod.forbid verify.business_user_priority_menu_plan.alignment verify.user_visible_business_fact_alignment verify.user_priority.browser_evidence.coverage verify.p1.daily_business_visible_contract.audit verify.p1.daily_business_form.usability.audit
	@echo "[OK] verify.user_priority.page_alignment.complete done"

.PHONY: verify.user_menu.config_policy
verify.user_menu.config_policy: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/user_menu_config_policy_probe.py

.PHONY: verify.user_menu.config_panel
verify.user_menu.config_panel: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/user_menu_config_panel_probe.py

history.legacy_user_access.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/history_legacy_user_access_projection_write.py

history.settlement_adjustment.runtime.probe: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/history_settlement_adjustment_runtime_probe.py

history.expense_claim.runtime.probe: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/history_expense_claim_runtime_probe.py

history.treasury_reconciliation.runtime.probe: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/history_treasury_reconciliation_runtime_probe.py

history.receipt_income.runtime.probe: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/history_receipt_income_runtime_probe.py

history.payment_execution.runtime.probe: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/history_payment_execution_runtime_probe.py

history.construction_diary.runtime.probe: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/history_construction_diary_runtime_probe.py

history.attachment.custody.probe: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/history_attachment_custody_probe.py

.PHONY: history.attachment.custody.probe.prod
history.attachment.custody.probe.prod: guard.prod.readonly check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/history_attachment_custody_probe.py

history.invoice_tax.runtime.probe: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/history_invoice_tax_runtime_probe.py

history.invoice_registration.runtime.probe: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/history_invoice_registration_runtime_probe.py

history.financing_loan.runtime.probe: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/history_financing_loan_runtime_probe.py

history.treasury.reconciliation.probe: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/history_treasury_reconciliation_probe.py

history.expense_deposit.runtime.probe: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/history_expense_deposit_runtime_probe.py

history.material_catalog.runtime.probe: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/history_material_catalog_runtime_probe.py

history.material_product.projection.probe: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/verify/material_product_projection_probe.py

history.purchase_contract.runtime.probe: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/history_purchase_contract_runtime_probe.py

history.general_contract.runtime.probe: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/history_general_contract_runtime_probe.py

.PHONY: menu.role_visibility.governance.probe
menu.role_visibility.governance.probe: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/menu_role_visibility_governance_probe.py

fresh_db.history_todo.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_history_todo_projection_write.py

fresh_db.treasury_ledger.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_treasury_ledger_projection_write.py

fresh_db.settlement_adjustment.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_settlement_adjustment_projection_write.py

fresh_db.expense_claim.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_expense_claim_projection_write.py

fresh_db.deposit_claim.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_deposit_claim_projection_write.py

fresh_db.deposit_claim_taxonomy.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_deposit_claim_taxonomy_projection_write.py

fresh_db.repayment_registration.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_repayment_registration_projection_write.py

fresh_db.contractor_project_repay.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_contractor_project_repay_projection_write.py

fresh_db.project_repay_company.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_project_repay_company_projection_write.py

fresh_db.deduction_bill.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_deduction_bill_projection_write.py

fresh_db.deduction_paid.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_deduction_paid_projection_write.py

fresh_db.deduction_paid_refund.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_deduction_paid_refund_projection_write.py

fresh_db.treasury_reconciliation.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_treasury_reconciliation_projection_write.py

fresh_db.receipt_income.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_receipt_income_projection_write.py

fresh_db.arrival_confirmation.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_arrival_confirmation_projection_write.py

fresh_db.fuel_card_operation.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_fuel_card_operation_projection_write.py

fresh_db.fuel_card_operation.projection.write.prod: guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_fuel_card_operation_projection_write.py

fresh_db.payment_execution.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_payment_execution_projection_write.py

fresh_db.payment_execution_taxonomy.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_payment_execution_taxonomy_projection_write.py

fresh_db.invoice_registration.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_invoice_registration_projection_write.py

fresh_db.receipt_invoice_line.output_visible_enrich.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/receipt_invoice_line_output_visible_enrich_write.py

fresh_db.financing_loan.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_financing_loan_projection_write.py

fresh_db.general_contract.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_general_contract_projection_write.py

fresh_db.construction_diary.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_construction_diary_projection_write.py

fresh_db.fund_account_between.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_fund_account_between_projection_write.py

fresh_db.fund_daily_report.projection.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_fund_daily_report_projection_write.py

history.project.lifecycle.continuity.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/history_project_lifecycle_continuity_adapter.py

migration.assets.fetch: guard.prod.forbid
	@python3 scripts/migration/migration_asset_fetch.py --lock "$(MIGRATION_ASSET_LOCK)" --asset-root "$(MIGRATION_ASSET_ROOT)"

migration.assets.verify_all: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/migration_asset_bus.py --asset-root "$(MIGRATION_ASSET_ROOT)" --catalog "$(MIGRATION_ASSET_ROOT)/manifest/migration_asset_catalog_v1.json" --verify-only --check

migration.assets.delivery_audit: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/migration_asset_delivery_audit.py --asset-root "$(MIGRATION_ASSET_ROOT)"

.PHONY: user_module.history_business_baseline.restore
user_module.history_business_baseline.restore: guard.prod.forbid check-compose-project check-compose-env
	@DB_NAME="$(DB_NAME)" MIGRATION_ASSET_ROOT="$(MIGRATION_ASSET_ROOT)" MIGRATION_ASSET_LOCK="$(MIGRATION_ASSET_LOCK)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/migration/user_module_history_business_baseline_restore.sh

.PHONY: migration.assets.user_acceptance_manifest_guard migration.assets.user_acceptance_manifest_guard.evidence migration.assets.user_acceptance_online_probe migration.assets.user_acceptance_browser_field_guard migration.assets.scbs_55_browser_full_visible_data_coverage migration.assets.scbsly_direct_project_menu_probe migration.assets.scbsly_direct_project_new_system_alignment_probe migration.assets.scbsly_direct_project_browser_menu_acceptance migration.assets.scbsly_direct_project_gap_matrix migration.assets.scbsly_direct_project_old_row_dump migration.assets.scbsly_direct_project_old_identity_lock migration.assets.scbsly_direct_project_replay_carrier_plan migration.assets.scbsly_direct_project_direct_acceptance_replay.write migration.assets.scbsly_direct_project_fuel_replay.write migration.assets.scbsly_direct_project_engineering_progress_replay.write migration.assets.scbsly_direct_project_rental_return_replay.write migration.assets.user_acceptance_replay.write migration.assets.live_old_system_business_data_strict_parity_gate verify.online_visible_surface.strict migration.assets.full_inventory migration.assets.replay_payload_gap_report migration.assets.payload_promotion_queue migration.assets.delivery_replay_requirement_lock migration.assets.full_scope_guard migration.assets.full_scope_refresh migration.assets.release_package migration.assets.release_package.verify
migration.assets.user_acceptance_manifest_guard: guard.prod.forbid
	@python3 scripts/verify/scbs55_user_acceptance_asset_manifest_guard.py

migration.assets.user_acceptance_manifest_guard.evidence: guard.prod.forbid
	@SCBS55_REQUIRE_ACCEPTANCE_EVIDENCE=1 python3 scripts/verify/scbs55_user_acceptance_asset_manifest_guard.py

migration.assets.user_acceptance_online_probe: guard.prod.forbid
	@python3 scripts/verify/scbs55_user_acceptance_online_probe.py

migration.assets.user_acceptance_browser_field_guard: guard.prod.forbid
	@node scripts/verify/scbs55_user_acceptance_browser_field_guard.js

migration.assets.scbs_55_browser_full_visible_data_coverage: guard.prod.forbid
	@DB_NAME="$(DB_NAME)" FRONTEND_URL="$${FRONTEND_URL:-http://1.95.85.92:18081}" E2E_LOGIN="$${E2E_LOGIN:-wutao}" E2E_PASSWORD="$${E2E_PASSWORD:-123456}" node scripts/verify/scbs_55_browser_full_visible_data_coverage.js

migration.assets.scbsly_direct_project_menu_probe: guard.prod.forbid
	@python3 scripts/verify/scbsly_direct_project_acceptance_menu_probe.py

migration.assets.scbsly_direct_project_new_system_alignment_probe: guard.prod.forbid
	@DB_NAME="$(DB_NAME)" node scripts/verify/scbsly_direct_project_new_system_alignment_probe.js

migration.assets.scbsly_direct_project_browser_menu_acceptance: guard.prod.forbid
	@DB_NAME="$(DB_NAME)" node scripts/verify/scbsly_direct_project_browser_menu_acceptance.js

migration.assets.scbsly_direct_project_gap_matrix: guard.prod.forbid
	@python3 scripts/verify/scbsly_direct_project_alignment_gap_matrix.py

migration.assets.scbsly_direct_project_old_row_dump: guard.prod.forbid
	@python3 scripts/verify/scbsly_direct_project_old_row_dump.py

migration.assets.scbsly_direct_project_old_identity_lock: guard.prod.forbid
	@python3 scripts/verify/scbsly_direct_project_old_identity_lock.py

migration.assets.scbsly_direct_project_replay_carrier_plan: guard.prod.forbid
	@python3 scripts/verify/scbsly_direct_project_replay_carrier_plan.py

migration.assets.scbsly_direct_project_direct_acceptance_replay.write: guard.prod.forbid
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" MIGRATION_SCBSLY_OLD_ROWS_DIR="$${MIGRATION_SCBSLY_OLD_ROWS_DIR:-$${SCBSLY_OLD_ROWS_DIR:-/mnt/artifacts/migration/live_old_system_strict_parity_gate/20260601T130457Z/scbsly_direct_project_old_rows}}" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/scbsly_direct_project_direct_acceptance_replay.py

migration.assets.scbsly_direct_project_fuel_replay.write: guard.prod.forbid
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" MIGRATION_SCBSLY_OLD_ROWS_DIR="$${MIGRATION_SCBSLY_OLD_ROWS_DIR:-$${SCBSLY_OLD_ROWS_DIR:-/tmp/scbsly_direct_project_old_pages_20260530}}" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/scbsly_direct_project_fuel_card_replay.py

migration.assets.scbsly_direct_project_engineering_progress_replay.write: guard.prod.forbid
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" MIGRATION_SCBSLY_OLD_ROWS_DIR="$${MIGRATION_SCBSLY_OLD_ROWS_DIR:-$${SCBSLY_OLD_ROWS_DIR:-/tmp/scbsly_direct_project_old_pages_20260530}}" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/scbsly_direct_project_engineering_progress_receipt_replay.py

migration.assets.scbsly_direct_project_rental_return_replay.write: guard.prod.forbid
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" MIGRATION_SCBSLY_OLD_ROWS_DIR="$${MIGRATION_SCBSLY_OLD_ROWS_DIR:-$${SCBSLY_OLD_ROWS_DIR:-/tmp/scbsly_direct_project_old_pages_20260530}}" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/scbsly_direct_project_rental_return_replay.py

migration.assets.user_acceptance_replay.write: guard.prod.forbid
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" MIGRATION_SCBS55_OLD_ROWS_DIR="$${MIGRATION_SCBS55_OLD_ROWS_DIR:-$${SCBS55_OLD_ROWS_DIR:-/tmp/scbs55_old_pages_20260530}}" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/scbs55_user_acceptance_replay.py

migration.assets.live_old_system_business_data_strict_parity_gate: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/validate_online_visible_surface_verification.sh

verify.online_visible_surface.strict: migration.assets.live_old_system_business_data_strict_parity_gate

migration.assets.full_inventory: guard.prod.forbid
	@python3 scripts/migration/scbs55_full_migration_asset_inventory.py

migration.assets.replay_payload_gap_report: guard.prod.forbid
	@python3 scripts/migration/scbs55_replay_payload_gap_report.py

migration.assets.payload_promotion_queue: guard.prod.forbid
	@python3 scripts/migration/scbs55_payload_promotion_queue.py

migration.assets.delivery_replay_requirement_lock: guard.prod.forbid
	@python3 scripts/migration/scbs55_delivery_replay_requirement_lock.py

migration.assets.full_scope_guard: guard.prod.forbid
	@python3 scripts/verify/scbs55_full_migration_asset_guard.py

migration.assets.full_scope_refresh: guard.prod.forbid
	@$(MAKE) migration.assets.full_inventory
	@$(MAKE) migration.assets.replay_payload_gap_report
	@$(MAKE) migration.assets.payload_promotion_queue
	@$(MAKE) migration.assets.delivery_replay_requirement_lock
	@$(MAKE) migration.assets.full_scope_guard

migration.assets.release_package: guard.prod.forbid
	@python3 scripts/migration/migration_asset_release_package.py --asset-root "$(MIGRATION_ASSET_ROOT)"

migration.assets.release_package.verify: guard.prod.forbid
	@package_path="$${MIGRATION_ASSET_RELEASE_PACKAGE:-$${MIGRATION_RELEASE_PACKAGE:-}}"; \
	  if [ -z "$$package_path" ]; then echo "MIGRATION_ASSET_RELEASE_PACKAGE is required"; exit 2; fi; \
	  cd "$$(dirname "$$package_path")" && sha256sum -c "$$(basename "$$package_path").sha256"; \
	  rm -rf /tmp/sce_migration_asset_release_verify; \
	  mkdir -p /tmp/sce_migration_asset_release_verify; \
	  tar -xzf "$$package_path" -C /tmp/sce_migration_asset_release_verify; \
	  cd /tmp/sce_migration_asset_release_verify && python3 scripts/migration/migration_asset_bus.py --asset-root migration_assets --catalog migration_assets/manifest/migration_asset_catalog_v1.json --verify-only --check; \
	  cd /tmp/sce_migration_asset_release_verify && python3 scripts/migration/migration_asset_delivery_audit.py --asset-root migration_assets

history.contract.core.gap.audit: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/history_contract_core_gap_audit.py

history.contract.partner.gap.audit: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/history_contract_partner_gap_audit.py

history.contract.strong_evidence.backtrace.audit: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/history_contract_strong_evidence_backtrace_audit.py

history.contract.direction_defer.audit: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/history_contract_direction_defer_audit.py

history.contract.direction_defer.recovery.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/history_contract_direction_defer_recovery_adapter.py

history.partner.master.targeted.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/history_partner_master_targeted_replay_adapter.py

history.contract.partner.recovery.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/history_contract_partner_recovery_adapter.py

history.partner.master.direction_defer.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/history_partner_master_direction_defer_replay_adapter.py

history.supplier.partner.targeted.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/history_supplier_partner_targeted_replay_adapter.py

history.outflow.partner.targeted.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/history_outflow_partner_targeted_replay_adapter.py

history.actual_outflow.partner.targeted.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/history_actual_outflow_partner_targeted_replay_adapter.py

history.receipt.parent.recovery.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/history_receipt_parent_recovery_adapter.py

history.receipt.partner.targeted.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/history_receipt_partner_targeted_replay_adapter.py

history.receipt_income.partner.targeted.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/history_receipt_income_partner_targeted_replay_adapter.py

history.expense_deposit.partner.targeted.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/history_expense_deposit_partner_targeted_replay_adapter.py

history.project_member.attachment.targeted.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/history_project_member_attachment_targeted_replay_adapter.py

history.payment_request.outflow.state_activation.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/history_payment_request_outflow_state_activation_adapter.py

history.payment_request.outflow.approved_recovery.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/history_payment_request_outflow_approved_recovery_adapter.py

history.payment_request.outflow.done_recovery.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/history_payment_request_outflow_done_recovery_adapter.py

fresh_db.outflow_request.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_outflow_request_replay_adapter.py

fresh_db.outflow_request.fact_coverage.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) MIGRATION_REPLAY_DB_ALLOWLIST="$(or $(MIGRATION_REPLAY_DB_ALLOWLIST),$(DB_NAME))" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_outflow_request_fact_coverage_write.py

fresh_db.actual_outflow.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_actual_outflow_replay_adapter.py

fresh_db.actual_outflow_residual.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_actual_outflow_residual_replay_adapter.py

fresh_db.actual_outflow_line.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_actual_outflow_line_replay_adapter.py

fresh_db.outflow_request_line.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_outflow_request_line_replay_adapter.py

fresh_db.receipt_invoice_line.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_receipt_invoice_line_replay_adapter.py

fresh_db.receipt_invoice_attachment.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_receipt_invoice_attachment_replay_adapter.py

fresh_db.legacy_attachment_backfill.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_attachment_backfill_replay_adapter.py

fresh_db.legacy_fund_daily_snapshot.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_fund_daily_snapshot_replay_adapter.py

fresh_db.legacy_fund_daily_line.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_fund_daily_line_replay_adapter.py

fresh_db.legacy_financing_loan.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_financing_loan_replay_adapter.py

fresh_db.legacy_receipt_income.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_receipt_income_replay_adapter.py

fresh_db.legacy_expense_deposit.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_expense_deposit_replay_adapter.py

.PHONY: fresh_db.legacy_income_invoice.replay.adapter
fresh_db.legacy_income_invoice.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_income_invoice_replay_adapter.py

.PHONY: fresh_db.legacy_income_invoice.replay.write
fresh_db.legacy_income_invoice.replay.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_legacy_income_invoice_replay_write.py

.PHONY: fresh_db.prepaid_tax.visible.refresh
fresh_db.prepaid_tax.visible.refresh: fresh_db.legacy_income_invoice.replay.adapter fresh_db.legacy_income_invoice.replay.write fresh_db.invoice_registration.projection.write
	@echo "[OK] fresh_db.prepaid_tax.visible.refresh done"

fresh_db.legacy_invoice_tax.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_invoice_tax_replay_adapter.py

.PHONY: fresh_db.legacy_invoice_tax.replay.write
fresh_db.legacy_invoice_tax.replay.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_legacy_invoice_tax_replay_write.py

fresh_db.legacy_tax_deduction.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_tax_deduction_replay_adapter.py

fresh_db.legacy_self_funding.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_self_funding_replay_adapter.py

fresh_db.legacy_project_fund_balance.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_project_fund_balance_replay_adapter.py

fresh_db.legacy_invoice_surcharge.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_invoice_surcharge_replay_adapter.py

fresh_db.legacy_supplier_contract_pricing.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_supplier_contract_pricing_replay_adapter.py

fresh_db.legacy_workflow_audit.replay.adapter: guard.prod.forbid check-compose-project check-compose-env
	@python3 scripts/migration/fresh_db_legacy_workflow_audit_replay_adapter.py

fresh_db.legacy_tax_deduction.replay.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_legacy_tax_deduction_replay_write.py

fresh_db.legacy_self_funding.replay.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_legacy_self_funding_replay_write.py

fresh_db.legacy_project_fund_balance.replay.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_legacy_project_fund_balance_replay_write.py

fresh_db.legacy_invoice_surcharge.replay.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_legacy_invoice_surcharge_replay_write.py

fresh_db.legacy_supplier_contract_pricing.replay.write: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MIGRATION_REPLAY_DB_ALLOWLIST="$(DB_NAME)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_legacy_supplier_contract_pricing_replay_write.py

.PHONY: bsi.create bsi.verify
bsi.create: ## Create/update Business Service Identity user (system-bound)
	@DB_NAME=$(DB_NAME) SERVICE_LOGIN=$(SERVICE_LOGIN) SERVICE_PASSWORD=$(SERVICE_PASSWORD) GROUP_XMLIDS="$(GROUP_XMLIDS)" \
		bash scripts/ops/bsi_create.sh

bsi.verify: ## Verify BSI can see business menu/root menu (system-bound)
	@DB_NAME=$(DB_NAME) SERVICE_LOGIN=$(SERVICE_LOGIN) MENU_XMLID=$(MENU_XMLID) ROOT_XMLID=$(ROOT_XMLID) \
		bash scripts/ops/bsi_verify.sh

.PHONY: diag.nav_root
diag.nav_root: check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/diag/nav_root_db_check.sh

# ======================================================
# ==================== DB / Demo =======================
# ======================================================
.PHONY: db.reset demo.reset db.branch db.create db.reset.manual
db.reset: guard.prod.forbid check-compose-project check-compose-env diag.project
	@$(RUN_ENV) bash scripts/db/reset.sh

# demo.reset 必须走 scripts/demo/reset.sh（含 seed/demo 安装）
demo.reset: guard.codex.fast.noheavy guard.prod.forbid check-compose-project check-compose-env diag.project
	@$(RUN_ENV) bash scripts/demo/reset.sh

# 兼容旧快捷命令：固定 sc_demo
.PHONY: db.demo.reset
db.demo.reset: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=sc_demo bash scripts/demo/reset.sh

db.branch:
	@bash scripts/db/branch_db.sh
db.create:
	@bash scripts/db/create.sh $(DB)
db.reset.manual: guard.prod.forbid check-compose-env
	@bash scripts/db/reset_manual.sh $(DB)

# ======================================================
# ==================== Verify / Gate ===================
# ======================================================
.PHONY: obs.coverage.report scene.export scene.snapshot.update scene.contract.export scene.package.export scene.pin.stable scene.rollback.stable audit.scene.config verify.baseline verify.demo verify.p0 verify.p0.flow verify.overview verify.overview.entry verify.overview.logic verify.portal.dashboard verify.portal.execute_button verify.portal.execute_button_smoke.container verify.portal.envelope_smoke.container verify.portal.fe_smoke.host verify.portal.fe_smoke.container verify.portal.view_state verify.portal.guard_groups verify.portal.menu_no_action verify.menu.scene_resolve verify.menu.scene_resolve.container verify.menu.scene_resolve.summary verify.menu.navigation_snapshot verify.menu.navigation_snapshot.container verify.portal.scene_registry verify.portal.capability_guard verify.portal.capability_policy_smoke verify.portal.semantic_route verify.portal.bridge.e2e verify.portal.scene_contract_smoke.container verify.portal.cross_stack_contract_smoke.container verify.portal.scene_layout_contract_smoke.container verify.portal.layout_stability_smoke.container verify.portal.workbench_tiles_smoke.container verify.portal.workspace_tiles_smoke.container verify.portal.workspace_tile_navigate_smoke.container verify.portal.menu_scene_key_smoke.container verify.portal.search_mvp_smoke.container verify.portal.sort_mvp_smoke.container verify.portal.tree_view_smoke.container verify.portal.kanban_view_smoke.container verify.portal.load_view_smoke.container verify.portal.view_contract_shape.container verify.portal.view_render_mode_smoke.container verify.portal.view_contract_coverage_smoke.container verify.portal.bootstrap_guard_smoke.container verify.portal.recordview_hud_smoke.container verify.portal.one2many_read_smoke.container verify.portal.one2many_edit_smoke.container verify.portal.attachment_list_smoke.container verify.portal.file_upload_smoke.container verify.portal.file_guard_smoke.container verify.portal.edit_tx_smoke.container verify.portal.write_conflict_smoke.container verify.portal.list_shell_title_smoke.container verify.portal.list_shell_no_meta_smoke.container verify.portal.scene_list_profile_smoke.container verify.portal.scene_default_sort_smoke.container verify.portal.scene_schema_smoke.container verify.portal.scene_semantic_smoke.container verify.portal.scene_tiles_semantic_smoke.container verify.portal.scene_targets_resolve_smoke.container verify.portal.scene_filters_semantic_smoke.container verify.portal.scene_versioning_smoke.container verify.portal.scene_target_smoke.container verify.portal.scene_diagnostics_smoke.container verify.portal.scene_warnings_guard.container verify.portal.scene_warnings_limit.container verify.portal.act_url_missing_scene_report.container verify.portal.scene_resolve_errors_debt_guard.container verify.portal.scene_contract_export_smoke.container verify.portal.scene_drift_guard.container verify.portal.scene_channel_smoke.container verify.portal.scene_rollback_smoke.container verify.portal.scene_snapshot_guard.container verify.portal.scene_package_dry_run_smoke.container verify.portal.scene_package_import_smoke.container verify.portal.scene_package_ui_smoke.container verify.portal.my_work_smoke.container verify.portal.payment_request_approval_smoke.container verify.portal.payment_request_approval_handoff_smoke.container verify.portal.v0_5.host verify.portal.v0_5.all verify.portal.v0_5.container verify.portal.v0_6.container verify.portal.ui.v0_7.container verify.portal.ui.v0_8.semantic.container verify.smart_core verify.e2e.contract verify.prod.guard prod.guard.mail_from prod.fix.mail_from gate.baseline gate.demo gate.full
.PHONY: verify.portal.scene_health_contract_smoke.container verify.portal.scene_auto_degrade_smoke.container
.PHONY: verify.portal.scene_health_pagination_smoke.container verify.portal.scene_governance_action_smoke.container verify.portal.scene_auto_degrade_notify_smoke.container
.PHONY: verify.portal.scene_governance_action_strict.container verify.portal.scene_auto_degrade_strict.container verify.portal.scene_auto_degrade_notify_strict.container verify.portal.scene_package_import_strict.container verify.portal.scene_observability_preflight.container verify.portal.scene_observability_preflight_smoke.container verify.portal.scene_observability_preflight.refresh.container verify.portal.scene_observability_preflight.latest verify.portal.scene_observability_preflight.report verify.portal.scene_observability_preflight.report.strict verify.portal.scene_observability_preflight.brief verify.portal.scene_observability_smoke.container verify.portal.scene_observability_gate_smoke.container verify.portal.scene_observability_strict.container
.PHONY: verify.portal.scene_package_dry_run_smoke.container verify.portal.scene_package_import_smoke.container verify.portal.scene_package_ui_smoke.container
.PHONY: verify.portal.scene_package_installed_smoke.container
.PHONY: verify.portal.ui.v0_8.semantic.strict.container
.PHONY: verify.platform_baseline verify.business_baseline verify.baseline.all gate.platform_baseline gate.business_baseline gate.baseline.all
verify.baseline: guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/baseline.sh
verify.demo: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=sc_demo bash scripts/verify/demo.sh
verify.p0: guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/p0_base.sh
verify.p0.flow: guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/p0_flow.sh
verify.platform_baseline: verify.baseline
	@echo "[OK] verify.platform_baseline done (env/platform baseline)"
verify.business_baseline: verify.p0.flow
	@echo "[OK] verify.business_baseline done (core+seed business baseline)"
verify.baseline.all: verify.platform_baseline verify.business_baseline
	@echo "[OK] verify.baseline.all done"
verify.overview: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/overview_rules.sh
verify.overview.entry: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/overview_entry.sh
verify.overview.logic: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/overview_logic.sh
verify.portal.dashboard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/portal_dashboard.sh
verify.portal.execute_button: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/portal_execute_button.sh
verify.portal.execute_button_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) MVP_VIEW_TYPE=$(MVP_VIEW_TYPE) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_execute_button_smoke.js"
verify.portal.fe_smoke.host: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) BASE_URL=$(BASE_URL) DB_NAME=$(DB_NAME) AUTH_TOKEN=$(AUTH_TOKEN) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) \
		bash scripts/diag/fe_smoke.sh
verify.portal.fe_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) AUTH_TOKEN=$(AUTH_TOKEN) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) bash /mnt/scripts/diag/fe_smoke.sh"
verify.portal.view_state: guard.prod.forbid check-compose-project check-compose-env
	@# RC smoke user: demo_pm/demo. svc_* accounts are service-only and may 401 in UI smokes.
	@$(RUN_ENV) node scripts/verify/fe_view_state_smoke.js
verify.portal.guard_groups: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) node scripts/verify/fe_guard_groups_smoke.js
verify.portal.menu_no_action: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) node scripts/verify/fe_menu_no_action_smoke.js
verify.menu.scene_resolve: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(if $(MENU_SCENE_ENFORCE_PREFIXES),MENU_SCENE_ENFORCE_PREFIXES="$(MENU_SCENE_ENFORCE_PREFIXES)") $(if $(MENU_SCENE_EXEMPTIONS),MENU_SCENE_EXEMPTIONS="$(MENU_SCENE_EXEMPTIONS)") node scripts/verify/fe_menu_scene_resolve_smoke.js
verify.menu.scene_resolve.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "API_BASE=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) $(if $(MENU_SCENE_ENFORCE_PREFIXES),MENU_SCENE_ENFORCE_PREFIXES='$(MENU_SCENE_ENFORCE_PREFIXES)') $(if $(MENU_SCENE_EXEMPTIONS),MENU_SCENE_EXEMPTIONS='$(MENU_SCENE_EXEMPTIONS)') node /mnt/scripts/verify/fe_menu_scene_resolve_smoke.js"
verify.menu.scene_resolve.summary: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) SUMMARY_PATH=artifacts/codex/summary.md ARTIFACTS_DIR=artifacts node scripts/verify/menu_scene_resolve_summary.js
verify.menu.navigation_snapshot: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) BASE_URL=$(BASE_URL) DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) node scripts/verify/menu_navigation_field_snapshot.js
verify.menu.navigation_snapshot.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "API_BASE=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) node /mnt/scripts/verify/menu_navigation_field_snapshot.js"
verify.phase_9_8.gate_summary: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) SUMMARY_PATH=artifacts/codex/summary.md ARTIFACTS_DIR=artifacts node scripts/verify/phase_9_8_gate_summary.js
verify.portal.scene_registry: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) node scripts/verify/fe_scene_registry_validate_smoke.js
verify.portal.capability_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) node scripts/verify/fe_capability_guard_smoke.js
verify.portal.capability_policy_smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) node scripts/verify/fe_capability_policy_smoke.js
verify.portal.semantic_route: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) node scripts/verify/fe_semantic_route_smoke.js
audit.scene.config: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) node /mnt/scripts/audit/scene_config_audit.js"
verify.portal.bridge.e2e: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) node /mnt/scripts/verify/portal_bridge_e2e_smoke.js"

.PHONY: verify.portal.payment_request_approval.prepare.container verify.portal.payment_request_approval_smoke.container verify.portal.payment_request_approval_handoff_smoke.container verify.portal.payment_request_approval_all_smoke.container verify.portal.payment_request_approval_field_consumer_audit verify.portal.business_real_user_browser_closure verify.portal.business_real_user_browser_reject_closure
verify.portal.payment_request_approval.prepare.container: guard.prod.forbid check-compose-project check-compose-env
	@if [ "$(PAYMENT_APPROVAL_NEED_UPGRADE)" = "1" ]; then \
	  CODEX_MODE=gate CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=$(DB_NAME) $(MAKE) --no-print-directory mod.upgrade; \
	else \
	  echo "[verify.portal.payment_request_approval.prepare.container] skip mod.upgrade (PAYMENT_APPROVAL_NEED_UPGRADE=$(PAYMENT_APPROVAL_NEED_UPGRADE))"; \
	fi
	@$(MAKE) --no-print-directory restart
	@sleep 5
	@AUTO_FIX_EXTENSION_MODULES=1 $(MAKE) --no-print-directory policy.ensure.extension_modules DB_NAME=$(DB_NAME)

.PHONY: verify.portal.business_real_user_browser_closure
verify.portal.business_real_user_browser_closure: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) FRONTEND_URL=$(or $(FRONTEND_URL),http://127.0.0.1:5174) bash scripts/verify/business_real_user_browser_closure.sh

.PHONY: verify.portal.business_real_user_browser_reject_closure
verify.portal.business_real_user_browser_reject_closure: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) FRONTEND_URL=$(or $(FRONTEND_URL),http://127.0.0.1:5174) BROWSER_CLOSURE_ACTION=reject bash scripts/verify/business_real_user_browser_closure.sh

.PHONY: verify.portal.payment_request_approval_smoke.container
verify.portal.payment_request_approval_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@if [ "$(PAYMENT_APPROVAL_SKIP_PREPARE)" != "1" ]; then \
	  $(MAKE) --no-print-directory verify.portal.payment_request_approval.prepare.container DB_NAME=$(DB_NAME); \
	fi
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) ROLE_FINANCE_LOGIN=$(or $(ROLE_FINANCE_LOGIN),demo_role_finance) ROLE_FINANCE_PASSWORD=$(or $(ROLE_FINANCE_PASSWORD),demo) python3 /mnt/scripts/verify/payment_request_approval_smoke.py"

.PHONY: verify.portal.payment_request_approval_handoff_smoke.container
verify.portal.payment_request_approval_handoff_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@if [ "$(PAYMENT_APPROVAL_SKIP_PREPARE)" != "1" ]; then \
	  $(MAKE) --no-print-directory verify.portal.payment_request_approval.prepare.container DB_NAME=$(DB_NAME); \
	fi
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) ROLE_FINANCE_LOGIN=$(or $(ROLE_FINANCE_LOGIN),demo_role_finance) ROLE_FINANCE_PASSWORD=$(or $(ROLE_FINANCE_PASSWORD),demo) ROLE_EXECUTIVE_LOGIN=$(or $(ROLE_EXECUTIVE_LOGIN),demo_role_executive) ROLE_EXECUTIVE_PASSWORD=$(or $(ROLE_EXECUTIVE_PASSWORD),demo) python3 /mnt/scripts/verify/payment_request_approval_handoff_smoke.py"

.PHONY: verify.portal.payment_request_approval_all_smoke.container
verify.portal.payment_request_approval_all_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(MAKE) --no-print-directory verify.portal.payment_request_approval.prepare.container DB_NAME=$(DB_NAME)
	@PAYMENT_APPROVAL_SKIP_PREPARE=1 $(MAKE) --no-print-directory verify.portal.payment_request_approval_smoke.container DB_NAME=$(DB_NAME)
	@PAYMENT_APPROVAL_SKIP_PREPARE=1 $(MAKE) --no-print-directory verify.portal.payment_request_approval_handoff_smoke.container DB_NAME=$(DB_NAME)
	@if [ "$(PAYMENT_APPROVAL_FIELD_AUDIT_STRICT)" = "1" ]; then \
	  $(MAKE) --no-print-directory verify.portal.payment_request_approval_field_consumer_audit; \
	else \
	  $(MAKE) --no-print-directory verify.portal.payment_request_approval_field_consumer_audit || \
	    echo "[warn] payment approval field consumer audit failed (set PAYMENT_APPROVAL_FIELD_AUDIT_STRICT=1 to block)"; \
	fi

.PHONY: verify.portal.payment_request_approval_field_consumer_audit
verify.portal.payment_request_approval_field_consumer_audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/payment_request_approval_field_consumer_audit.py
verify.portal.v0_5.host: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MVP_MENU_XMLID=$(MVP_MENU_XMLID) ROOT_XMLID=$(ROOT_XMLID) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) ARTIFACTS_DIR=$(ARTIFACTS_DIR) \
		node scripts/verify/fe_mvp_list_smoke.js
verify.portal.v0_5.all: verify.portal.view_state verify.portal.v0_5.container
	@echo "[OK] verify.portal.v0_5.all done"
verify.portal.v0_5.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MENU_XMLID=$(MVP_MENU_XMLID) ROOT_XMLID=$(ROOT_XMLID) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) node /mnt/scripts/verify/fe_mvp_list_smoke.js"
verify.portal.v0_6.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) ROOT_XMLID=$(ROOT_XMLID) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) CREATE_NAME=$(CREATE_NAME) UPDATE_NAME=$(UPDATE_NAME) node /mnt/scripts/verify/fe_mvp_write_smoke.js"
verify.portal.recordview_hud_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) ROOT_XMLID=$(ROOT_XMLID) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) node /mnt/scripts/verify/fe_recordview_hud_smoke.js"
verify.portal.load_view_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) RECORD_ID=$(RECORD_ID) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) node /mnt/scripts/verify/fe_load_view_smoke.js"
verify.portal.view_contract_shape.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) MVP_VIEW_TYPE=$(MVP_VIEW_TYPE) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_view_contract_shape_smoke.js"
verify.portal.view_render_mode_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) MVP_VIEW_TYPE=$(MVP_VIEW_TYPE) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_view_render_mode_smoke.js"
verify.portal.view_contract_coverage_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) MVP_VIEW_TYPE=$(MVP_VIEW_TYPE) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) ALLOWED_MISSING=$(ALLOWED_MISSING) node /mnt/scripts/verify/fe_view_contract_coverage_smoke.js"
verify.portal.bootstrap_guard_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) EXPECT_STATUS=$(EXPECT_STATUS) node /mnt/scripts/verify/fe_bootstrap_guard_smoke.js"
verify.portal.one2many_read_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) MVP_VIEW_TYPE=$(MVP_VIEW_TYPE) RECORD_ID=$(RECORD_ID) ONE2MANY_FIELD=$(ONE2MANY_FIELD) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_one2many_read_smoke.js"
verify.portal.one2many_edit_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) MVP_VIEW_TYPE=$(MVP_VIEW_TYPE) RECORD_ID=$(RECORD_ID) ONE2MANY_FIELD=$(ONE2MANY_FIELD) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_one2many_edit_smoke.js"
verify.portal.attachment_list_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) RECORD_ID=$(RECORD_ID) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_attachment_list_smoke.js"
verify.portal.file_upload_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) RECORD_ID=$(RECORD_ID) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_file_upload_smoke.js"
verify.portal.file_guard_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) RECORD_ID=$(RECORD_ID) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_file_guard_smoke.js"
verify.portal.edit_tx_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) RECORD_ID=$(RECORD_ID) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_edit_tx_smoke.js"
verify.portal.write_conflict_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) RECORD_ID=$(RECORD_ID) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_write_conflict_smoke.js"
verify.portal.search_mvp_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_search_mvp_smoke.js"
verify.portal.sort_mvp_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_sort_mvp_smoke.js"
verify.portal.tree_view_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) TREE_GROUPED_SNAPSHOT_UPDATE=$(TREE_GROUPED_SNAPSHOT_UPDATE) TREE_GROUPED_BASELINE=$(TREE_GROUPED_BASELINE) REQUIRE_GROUPED_ROWS=$(REQUIRE_GROUPED_ROWS) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_tree_view_smoke.js"
.PHONY: verify.portal.ar_ap_project_summary_smoke.container
verify.portal.ar_ap_project_summary_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) node /mnt/scripts/verify/fe_ar_ap_project_summary_smoke.js"
.PHONY: verify.portal.ar_ap_company_summary_smoke.container
verify.portal.ar_ap_company_summary_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) node /mnt/scripts/verify/fe_ar_ap_company_summary_smoke.js"
verify.portal.kanban_view_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_kanban_view_smoke.js"
verify.portal.scene_contract_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_contract_smoke.js"

verify.portal.cross_stack_contract_smoke.container: guard.prod.forbid check-compose-project check-compose-env verify.extension_modules.guard
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "REPO_ROOT=/mnt BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) node /mnt/scripts/verify/fe_cross_stack_contract_smoke.js"

verify.portal.envelope_smoke.container: verify.portal.scene_contract_smoke.container verify.portal.my_work_smoke.container verify.portal.execute_button_smoke.container verify.portal.cross_stack_contract_smoke.container
	@echo "[OK] verify.portal.envelope_smoke.container done"

verify.portal.scene_layout_contract_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_layout_contract_smoke.js"

verify.portal.layout_stability_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_layout_stability_smoke.js"
verify.portal.workbench_tiles_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_workbench_tiles_smoke.js"

verify.portal.workspace_tiles_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_workspace_tiles_smoke.js"

verify.portal.workspace_tile_navigate_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_workspace_tile_navigate_smoke.js"
verify.portal.menu_scene_key_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_menu_scene_key_smoke.js"
verify.portal.list_shell_title_smoke.container: guard.prod.forbid
	@REPO_ROOT="$(PWD)" node scripts/verify/fe_list_shell_title_smoke.js
verify.portal.list_shell_no_meta_smoke.container: guard.prod.forbid
	@REPO_ROOT="$(PWD)" node scripts/verify/fe_list_shell_no_meta_smoke.js
verify.portal.scene_list_profile_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_list_profile_smoke.js"
verify.portal.scene_default_sort_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_default_sort_smoke.js"
verify.portal.scene_schema_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_schema_smoke.js"
verify.portal.scene_semantic_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_semantic_smoke.js"
verify.portal.scene_tiles_semantic_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_tiles_semantic_smoke.js"
verify.portal.scene_targets_resolve_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_targets_resolve_smoke.js"
verify.portal.scene_filters_semantic_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_filters_semantic_smoke.js"
verify.portal.my_work_smoke.container: guard.prod.forbid check-compose-project check-compose-env verify.extension_modules.guard
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) node /mnt/scripts/verify/fe_my_work_smoke.js"

.PHONY: verify.portal.usage_track_concurrency_smoke.container
verify.portal.usage_track_concurrency_smoke.container: guard.prod.forbid check-compose-project check-compose-env verify.extension_modules.guard
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) USAGE_TRACK_REQUEST_TOTAL=$(USAGE_TRACK_REQUEST_TOTAL) USAGE_TRACK_CONCURRENCY=$(USAGE_TRACK_CONCURRENCY) USAGE_TRACK_SCENE_KEY=$(USAGE_TRACK_SCENE_KEY) node /mnt/scripts/verify/fe_usage_track_concurrency_smoke.js"
verify.portal.scene_versioning_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_versioning_smoke.js"
verify.portal.scene_target_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_target_smoke.js"
verify.portal.scene_diagnostics_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_diagnostics_smoke.js"
verify.portal.scene_warnings_guard.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) DENY_WARNING_CODES=ACT_URL_MISSING_SCENE node /mnt/scripts/verify/scene_warnings_guard_summary.js"
verify.portal.scene_warnings_limit.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) SC_WARN_ACT_URL_LEGACY_MAX=$(SC_WARN_ACT_URL_LEGACY_MAX) node /mnt/scripts/verify/scene_warnings_guard_summary.js"
verify.portal.act_url_missing_scene_report.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) node /mnt/scripts/verify/act_url_missing_scene_report.js"
verify.portal.scene_health_contract_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_health_contract_smoke.js"
verify.portal.scene_auto_degrade_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_auto_degrade_smoke.js"
verify.portal.scene_health_pagination_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_health_pagination_smoke.js"
verify.portal.scene_governance_action_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_portal_scene_governance_action_smoke.js"
verify.portal.scene_governance_action_strict.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "REQUIRE_GOVERNANCE_LOG=1 BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_portal_scene_governance_action_smoke.js"
verify.portal.scene_auto_degrade_notify_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_auto_degrade_notify_smoke.js"
verify.portal.scene_auto_degrade_notify_strict.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "REQUIRE_NOTIFY_SENT=1 REQUIRE_NOTIFY_AUDIT=1 BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_auto_degrade_notify_smoke.js"
verify.portal.scene_auto_degrade_strict.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "REQUIRE_GOVERNANCE_LOG=1 BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_auto_degrade_smoke.js"
verify.portal.scene_package_dry_run_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) node /mnt/scripts/verify/fe_scene_package_dry_run_smoke.js"
verify.portal.scene_package_import_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) node /mnt/scripts/verify/fe_scene_package_import_smoke.js"
verify.portal.scene_observability_preflight.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "SCENE_OBSERVABILITY_PREFLIGHT_STRICT=$(SCENE_OBSERVABILITY_PREFLIGHT_STRICT) BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) node /mnt/scripts/verify/fe_scene_observability_preflight_smoke.js"
verify.portal.scene_observability_preflight_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "SCENE_OBSERVABILITY_PREFLIGHT_STRICT=0 BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) node /mnt/scripts/verify/fe_scene_observability_preflight_smoke.js"
verify.portal.scene_observability_preflight.refresh.container: verify.portal.scene_observability_preflight_smoke.container verify.portal.scene_observability_preflight.report
	@echo \"[OK] verify.portal.scene_observability_preflight.refresh.container done\"
verify.portal.scene_observability_preflight.latest: guard.prod.forbid
	@latest="$$(ls -1dt artifacts/codex/portal-scene-observability-preflight-v10_4/* 2>/dev/null | head -n 1)"; \
	if [ -z "$$latest" ]; then \
	  echo "❌ no preflight artifacts found under artifacts/codex/portal-scene-observability-preflight-v10_4"; \
	  exit 2; \
	fi; \
	echo "$$latest"
verify.portal.scene_observability_preflight.report: guard.prod.forbid
	@python3 scripts/verify/scene_observability_preflight_report.py
verify.portal.scene_observability_preflight.report.strict: guard.prod.forbid
	@python3 scripts/verify/scene_observability_preflight_report.py --strict
verify.portal.scene_observability_preflight.brief: guard.prod.forbid
	@python3 scripts/verify/scene_observability_preflight_brief.py
verify.portal.scene_observability_smoke.container: verify.portal.scene_governance_action_smoke.container verify.portal.scene_auto_degrade_smoke.container verify.portal.scene_auto_degrade_notify_smoke.container verify.portal.scene_package_import_smoke.container
	@echo \"[OK] verify.portal.scene_observability_smoke.container done\"
verify.portal.scene_observability_gate_smoke.container: verify.portal.scene_observability.structure_guard verify.portal.scene_observability_preflight_smoke.container verify.portal.scene_observability_smoke.container
	@echo \"[OK] verify.portal.scene_observability_gate_smoke.container done\"
verify.portal.scene_package_import_strict.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "REQUIRE_GOVERNANCE_LOG=1 BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) node /mnt/scripts/verify/fe_scene_package_import_smoke.js"
verify.portal.scene_observability_strict.container: verify.portal.scene_observability.structure_guard verify.portal.scene_observability_preflight.container verify.portal.scene_observability_preflight.report.strict verify.portal.scene_governance_action_strict.container verify.portal.scene_auto_degrade_strict.container verify.portal.scene_auto_degrade_notify_strict.container verify.portal.scene_package_import_strict.container
	@echo \"[OK] verify.portal.scene_observability_strict.container done\"
verify.portal.scene_package_ui_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) node /mnt/scripts/verify/fe_portal_scene_package_ui_smoke.js"
verify.portal.scene_package_installed_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) node /mnt/scripts/verify/fe_scene_package_installed_smoke.js"
verify.portal.scene_resolve_errors_debt_guard.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "DEBT_ROOT=/mnt DEBT_OUT=/mnt/artifacts/resolve_errors_debt.latest.json BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_resolve_errors_debt_guard.js"
verify.portal.scene_contract_export_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "SCENE_CHANNEL=$(SCENE_CHANNEL) CONTRACT_OUT=/mnt/artifacts/scenes/scene_contract.latest.json BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_contract_export_smoke.js"
verify.portal.scene_drift_guard.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "SCENE_CHANNEL=$(SCENE_CHANNEL) SCENE_USE_PINNED=$(SCENE_USE_PINNED) DRIFT_ROOT=/mnt DRIFT_OUT=/mnt/artifacts/scenes/scene_drift_report.latest.json CONTRACT_OUT=/mnt/artifacts/scenes/scene_contract.latest.json CONTRACT_DIFF=/mnt/artifacts/scenes/scene_contract.diff.txt BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_drift_guard.js"
verify.portal.scene_channel_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "SCENE_CHANNEL=$(SCENE_CHANNEL) BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_channel_smoke.js"
verify.portal.scene_rollback_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "SCENE_CHANNEL=$(SCENE_CHANNEL) SCENE_USE_PINNED=$(SCENE_USE_PINNED) BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_rollback_smoke.js"
verify.portal.scene_snapshot_guard.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "SNAPSHOT_ROOT=/mnt/extra-addons SNAPSHOT_OUT=/mnt/extra-addons/artifacts/scenes/LATEST.snapshot.json BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/extra-addons/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) SNAPSHOT_UPDATE=$(SNAPSHOT_UPDATE) node /mnt/scripts/verify/fe_scene_snapshot_guard.js"
scene.contract.export: guard.prod.forbid
	@CONTRACT_ROOT="$(PWD)" SCENE_CHANNEL=$(SCENE_CHANNEL) BASE_URL=http://localhost:8070 ARTIFACTS_DIR=artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) CONTRACT_OUT=docs/contract/exports/scenes/$(SCENE_CHANNEL)/LATEST.json CONTRACT_LATEST=docs/contract/exports/scenes/$(SCENE_CHANNEL)/LATEST.json node scripts/verify/fe_scene_contract_export.js
scene.package.export: guard.prod.forbid
	@CONTRACT_ROOT="$(PWD)" PACKAGE_NAME="$(PACKAGE_NAME)" PACKAGE_VERSION="$(PACKAGE_VERSION)" SCENE_CHANNEL=$(SCENE_CHANNEL) BASE_URL=http://localhost:8070 ARTIFACTS_DIR=artifacts DB_NAME=$(DB_NAME) node scripts/verify/fe_scene_package_export.js
scene.pin.stable: guard.prod.forbid
	@test -f docs/contract/exports/scenes/stable/LATEST.json || (echo "❌ stable/LATEST.json missing" && exit 2)
	@cp docs/contract/exports/scenes/stable/LATEST.json docs/contract/exports/scenes/stable/PINNED.json
	@echo "[scene.pin.stable] stable/PINNED.json updated"
scene.rollback.stable: guard.prod.forbid
	@SCENE_CHANNEL=stable SCENE_USE_PINNED=1 $(MAKE) restart
scene.export: guard.prod.forbid
	@SNAPSHOT_ROOT="$(PWD)" BASE_URL=http://localhost:8070 ARTIFACTS_DIR=artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) SNAPSHOT_OUT=docs/contract/snapshots/scenes/LATEST.json node scripts/verify/fe_scene_snapshot_guard.js
scene.snapshot.update: guard.prod.forbid
	@SNAPSHOT_ROOT="$(PWD)" BASE_URL=http://localhost:8070 ARTIFACTS_DIR=artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) SNAPSHOT_UPDATE=1 SNAPSHOT_BASELINE=docs/contract/snapshots/scenes/scenes.v0_9_8.json node scripts/verify/fe_scene_snapshot_guard.js

obs.coverage.report:
	@node scripts/ops/coverage_trend.js

# v0.8.4 aggregate gate
.PHONY: verify.portal.ui.v0_8_4.container
verify.portal.ui.v0_8_4.container: verify.portal.ui.v0_8.semantic.container verify.portal.execute_button_smoke.container verify.portal.bootstrap_guard_smoke.container verify.portal.view_contract_coverage_smoke.container
	@echo \"[OK] verify.portal.ui.v0_8_4.container done\"
verify.portal.ui.v0_7.container: verify.portal.view_state verify.portal.guard_groups verify.portal.menu_no_action verify.portal.load_view_smoke.container verify.portal.fe_smoke.container verify.portal.v0_6.container verify.portal.recordview_hud_smoke.container
	@echo \"[OK] verify.portal.ui.v0_7.container done\"
verify.portal.ui.v0_8.semantic.container: verify.frontend.suggested_action.all verify.portal.view_contract_shape.container verify.portal.view_render_mode_smoke.container verify.portal.view_contract_coverage_smoke.container verify.portal.envelope_smoke.container verify.portal.scene_layout_contract_smoke.container verify.portal.layout_stability_smoke.container verify.portal.workbench_tiles_smoke.container verify.portal.workspace_tiles_smoke.container verify.portal.workspace_tile_navigate_smoke.container verify.portal.menu_scene_key_smoke.container verify.portal.list_shell_title_smoke.container verify.portal.list_shell_no_meta_smoke.container verify.portal.scene_list_profile_smoke.container verify.portal.scene_default_sort_smoke.container verify.portal.scene_schema_smoke.container verify.portal.scene_semantic_smoke.container verify.portal.scene_tiles_semantic_smoke.container verify.portal.scene_targets_resolve_smoke.container verify.portal.scene_versioning_smoke.container verify.portal.scene_diagnostics_smoke.container verify.portal.scene_health_contract_smoke.container verify.portal.scene_health_pagination_smoke.container verify.portal.scene_governance_action_smoke.container verify.portal.scene_auto_degrade_smoke.container verify.portal.scene_auto_degrade_notify_smoke.container verify.portal.scene_package_dry_run_smoke.container verify.portal.scene_package_import_smoke.container verify.portal.scene_resolve_errors_debt_guard.container verify.portal.scene_contract_export_smoke.container verify.portal.scene_drift_guard.container verify.portal.scene_channel_smoke.container verify.portal.scene_rollback_smoke.container verify.portal.scene_snapshot_guard.container verify.portal.scene_target_smoke.container
	@echo \"[OK] verify.portal.ui.v0_8.semantic.container done\"
verify.portal.ui.v0_8.semantic.strict.container: verify.portal.ui.v0_8.semantic.container verify.portal.scene_observability_strict.container
	@echo \"[OK] verify.portal.ui.v0_8.semantic.strict.container done\"
verify.smart_core: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/smart_core.sh

.PHONY: verify.smart_core.minimum_surface.legacy_group_guard verify.smart_core.minimum_surface.handler_guard verify.smart_core.minimum_surface.frontend_runtime_config_guard verify.smart_core.minimum_surface.contract_guard verify.smart_core.minimum_surface.owner_startup_smoke verify.smart_core.minimum_surface.same_route_guard verify.smart_core.minimum_surface.order_regression_guard verify.smart_core.minimum_surface.app_open_regression_guard verify.smart_core.minimum_surface.nav_isolation_guard verify.smart_core.minimum_surface
verify.smart_core.minimum_surface.legacy_group_guard: guard.prod.forbid
	@python3 scripts/verify/smart_core_legacy_group_required_groups_guard.py

verify.smart_core.minimum_surface.handler_guard: guard.prod.forbid
	@python3 scripts/verify/smart_core_minimum_handler_surface_guard.py

verify.smart_core.minimum_surface.frontend_runtime_config_guard: guard.prod.forbid
	@python3 scripts/verify/frontend_platform_runtime_config_guard.py

verify.smart_core.minimum_surface.contract_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/smart_core_minimum_contract_surface_guard.py"

verify.smart_core.minimum_surface.owner_startup_smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/smart_core_owner_startup_smoke.py"

verify.smart_core.minimum_surface.same_route_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/smart_core_same_route_residency_guard.py"

verify.smart_core.minimum_surface.order_regression_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/smart_core_minimum_surface_order_regression_guard.py"

verify.smart_core.minimum_surface.app_open_regression_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) ROLE_OWNER_LOGIN=$(or $(ROLE_OWNER_LOGIN),demo_role_owner) ROLE_OWNER_PASSWORD=$(or $(ROLE_OWNER_PASSWORD),demo) python3 /mnt/scripts/verify/smart_core_app_open_fallback_regression_guard.py"

verify.smart_core.minimum_surface.nav_isolation_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/smart_core_platform_minimum_nav_isolation_guard.py"

verify.smart_core.minimum_surface: verify.smart_core.minimum_surface.legacy_group_guard verify.smart_core.minimum_surface.handler_guard verify.smart_core.minimum_surface.frontend_runtime_config_guard verify.smart_core.minimum_surface.contract_guard verify.smart_core.minimum_surface.owner_startup_smoke verify.smart_core.minimum_surface.same_route_guard verify.smart_core.minimum_surface.order_regression_guard verify.smart_core.minimum_surface.app_open_regression_guard verify.smart_core.minimum_surface.nav_isolation_guard
	@echo "[OK] verify.smart_core.minimum_surface done"

verify.prod.guard: check-compose-env
	@bash scripts/verify/prod_guard_smoke.sh

# ------------------ Prod Guards ------------------
prod.guard.mail_from: check-compose-project check-compose-env
	@DB_NAME=$(DB_NAME) bash scripts/prod/guard_mail_from.sh

prod.fix.mail_from: guard.prod.danger check-compose-project check-compose-env
	@DB_NAME=$(DB_NAME) bash scripts/prod/fix_mail_from.sh

gate.baseline: guard.codex.fast.noheavy guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/db/reset.sh
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/baseline.sh
gate.platform_baseline: gate.baseline
	@echo "[OK] gate.platform_baseline done"
gate.business_baseline: guard.codex.fast.noheavy guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/p0_flow.sh
	@echo "[OK] gate.business_baseline done"
gate.baseline.all: gate.platform_baseline gate.business_baseline
	@echo "[OK] gate.baseline.all done"

gate.demo: guard.codex.fast.noheavy guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=sc_demo bash scripts/demo/reset.sh
	@$(RUN_ENV) DB_NAME=sc_demo bash scripts/verify/demo.sh

# ======================================================
# ==================== Module Ops ======================
# ======================================================
.PHONY: mod.install mod.upgrade
mod.install: guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/mod/install.sh
mod.upgrade: guard.codex.fast.upgrade guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/mod/upgrade.sh

# ======================================================
# ==================== Policy Ops ======================
# ======================================================
.PHONY: db.frontend.acceptance.ensure demo.frontend.fixture verify.frontend.fixture verify.frontend.fixture.guard verify.frontend.fixture.browser verify.frontend.navigation.access verify.frontend.page_identity.browser verify.frontend.page_identity.deep.browser policy.apply.business_full policy.apply.role_matrix policy.ensure.role_surface_demo smoke.business_full smoke.role_matrix verify.portal.role_surface_preflight.container verify.portal.role_surface_smoke.container p2.smoke p3.smoke p3.audit codex.preflight codex.merge codex.rollback codex.pr.body codex.release.note db.policy stage.preflight stage.run ops.auth.dev.apply ops.auth.dev.rollback ops.auth.dev.verify
FRONTEND_ACCEPTANCE_DB := $(if $(filter command line,$(origin DB_NAME)),$(DB_NAME),sc_frontend_acceptance)

db.frontend.acceptance.ensure: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(FRONTEND_ACCEPTANCE_DB) SC_ENVIRONMENT=acceptance SC_ALLOW_DEMO_DATA=1 bash scripts/demo/frontend_acceptance_db_ensure.sh

demo.frontend.fixture: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(FRONTEND_ACCEPTANCE_DB) SC_ENVIRONMENT=acceptance SC_ALLOW_DEMO_DATA=1 bash scripts/demo/frontend_productization_fixture.sh

verify.frontend.fixture: guard.prod.forbid check-compose-project check-compose-env
	@python3 -m py_compile addons/smart_construction_demo/tools/frontend_productization_fixture.py scripts/verify/frontend_productization_fixture.py scripts/verify/frontend_productization_fixture_nonfixture_regression.py scripts/verify/frontend_productization_history_fingerprint.py
	@$(RUN_ENV) DB_NAME=$(FRONTEND_ACCEPTANCE_DB) SC_ENVIRONMENT=acceptance SC_ALLOW_DEMO_DATA=1 bash scripts/verify/frontend_productization_fixture.sh
	@$(MAKE) --no-print-directory verify.frontend.fixture.browser DB_NAME=$(FRONTEND_ACCEPTANCE_DB)

verify.frontend.fixture.guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/verify/frontend_productization_fixture_guard.sh

verify.frontend.fixture.browser: guard.prod.forbid check-compose-project check-compose-env
	@set -e; \
	runtime_output="$$( $(RUN_ENV) DB_NAME=$(FRONTEND_ACCEPTANCE_DB) SC_ENVIRONMENT=acceptance SC_ALLOW_DEMO_DATA=1 bash scripts/ops/odoo_shell_exec.sh < scripts/verify/frontend_productization_fixture_runtime_ids.py 2>&1 )"; \
	action_line="$$(echo "$$runtime_output" | grep '^FRONTEND_FIXTURE_PAYMENT_ACTION_ID=' | tail -1)"; \
	menu_line="$$(echo "$$runtime_output" | grep '^FRONTEND_FIXTURE_PAYMENT_MENU_ID=' | tail -1)"; \
	record_a_line="$$(echo "$$runtime_output" | grep '^FRONTEND_FIXTURE_PAYMENT_RECORD_A_ID=' | tail -1)"; \
	record_c_line="$$(echo "$$runtime_output" | grep '^FRONTEND_FIXTURE_PAYMENT_RECORD_C_ID=' | tail -1)"; \
	test -n "$$action_line" -a -n "$$menu_line" -a -n "$$record_a_line" -a -n "$$record_c_line"; \
	export "$$action_line" "$$menu_line" "$$record_a_line" "$$record_c_line"; \
	$(MAKE) --no-print-directory backend.acceptance.up; $(MAKE) --no-print-directory frontend.acceptance.up; trap '$(MAKE) --no-print-directory frontend.acceptance.down; $(MAKE) --no-print-directory backend.acceptance.down' EXIT; $(RUN_ENV) DB_NAME=$(FRONTEND_ACCEPTANCE_DB) SC_ENVIRONMENT=acceptance SC_ALLOW_DEMO_DATA=1 FRONTEND_URL=$${FRONTEND_URL:-http://127.0.0.1:5175} FRONTEND_FIXTURE_PAYMENT_ACTION_ID=$${FRONTEND_FIXTURE_PAYMENT_ACTION_ID} FRONTEND_FIXTURE_PAYMENT_MENU_ID=$${FRONTEND_FIXTURE_PAYMENT_MENU_ID} FRONTEND_FIXTURE_PAYMENT_RECORD_A_ID=$${FRONTEND_FIXTURE_PAYMENT_RECORD_A_ID} FRONTEND_FIXTURE_PAYMENT_RECORD_C_ID=$${FRONTEND_FIXTURE_PAYMENT_RECORD_C_ID} node scripts/verify/frontend_productization_fixture_browser.mjs

verify.frontend.navigation.access: guard.prod.forbid check-compose-project check-compose-env
	@set -e; \
	runtime_output="$$( $(RUN_ENV) DB_NAME=$(FRONTEND_ACCEPTANCE_DB) SC_ENVIRONMENT=acceptance SC_ALLOW_DEMO_DATA=1 bash scripts/ops/odoo_shell_exec.sh < scripts/verify/frontend_navigation_access_runtime_ids.py 2>&1 )"; \
	for key in PLAN_ACTION PLAN_MENU PLAN_REPORT_ACTION PLAN_REPORT_MENU TENDER_ACTION TENDER_MENU; do \
		line="$$(echo "$$runtime_output" | grep "^FRONTEND_NAV_ACCESS_$${key}_ID=" | tail -1)"; test -n "$$line"; export "$$line"; \
	done; \
	$(MAKE) --no-print-directory backend.acceptance.up; $(MAKE) --no-print-directory frontend.acceptance.up; trap '$(MAKE) --no-print-directory frontend.acceptance.down; $(MAKE) --no-print-directory backend.acceptance.down' EXIT; \
	$(RUN_ENV) DB_NAME=$(FRONTEND_ACCEPTANCE_DB) SC_ENVIRONMENT=acceptance SC_ALLOW_DEMO_DATA=1 FRONTEND_URL=$${FRONTEND_URL:-http://127.0.0.1:5175} \
	FRONTEND_NAV_ACCESS_PLAN_ACTION_ID=$${FRONTEND_NAV_ACCESS_PLAN_ACTION_ID} FRONTEND_NAV_ACCESS_PLAN_MENU_ID=$${FRONTEND_NAV_ACCESS_PLAN_MENU_ID} \
	FRONTEND_NAV_ACCESS_PLAN_REPORT_ACTION_ID=$${FRONTEND_NAV_ACCESS_PLAN_REPORT_ACTION_ID} FRONTEND_NAV_ACCESS_PLAN_REPORT_MENU_ID=$${FRONTEND_NAV_ACCESS_PLAN_REPORT_MENU_ID} \
	FRONTEND_NAV_ACCESS_TENDER_ACTION_ID=$${FRONTEND_NAV_ACCESS_TENDER_ACTION_ID} FRONTEND_NAV_ACCESS_TENDER_MENU_ID=$${FRONTEND_NAV_ACCESS_TENDER_MENU_ID} \
	node scripts/verify/frontend_navigation_access_consistency_browser.mjs

verify.frontend.page_identity.browser: guard.prod.forbid check-compose-project check-compose-env
	@set -e; \
	runtime_output="$$( $(RUN_ENV) DB_NAME=$(FRONTEND_ACCEPTANCE_DB) SC_ENVIRONMENT=acceptance SC_ALLOW_DEMO_DATA=1 bash scripts/ops/odoo_shell_exec.sh < scripts/verify/frontend_page_identity_runtime_metadata.py 2>&1 )"; \
	action_xmlids_line="$$(echo "$$runtime_output" | grep '^FRONTEND_PAGE_IDENTITY_ACTION_XMLIDS_JSON=' | tail -1)"; \
	test -n "$$action_xmlids_line"; export "$$action_xmlids_line"; \
	$(MAKE) --no-print-directory backend.acceptance.up; \
	$(MAKE) --no-print-directory frontend.acceptance.up; \
	trap '$(MAKE) --no-print-directory frontend.acceptance.down; $(MAKE) --no-print-directory backend.acceptance.down' EXIT; \
	$(RUN_ENV) DB_NAME=$(FRONTEND_ACCEPTANCE_DB) SC_ENVIRONMENT=acceptance SC_ALLOW_DEMO_DATA=1 FRONTEND_URL=$${FRONTEND_URL:-http://127.0.0.1:5175} ARTIFACTS_DIR=artifacts/frontend-page-identity FRONTEND_PAGE_IDENTITY_INVENTORY_PATH=docs/frontend_productization/frontend_surface_inventory_v1.csv FRONTEND_PAGE_IDENTITY_ACTION_XMLIDS_JSON="$${FRONTEND_PAGE_IDENTITY_ACTION_XMLIDS_JSON}" node frontend/apps/web/scripts/frontend_product_maturity_audit.mjs

verify.frontend.page_identity.deep.browser: guard.prod.forbid check-compose-project check-compose-env
	@set -e; \
	runtime_output="$$( $(RUN_ENV) DB_NAME=$(FRONTEND_ACCEPTANCE_DB) SC_ENVIRONMENT=acceptance SC_ALLOW_DEMO_DATA=1 bash scripts/ops/odoo_shell_exec.sh < scripts/verify/frontend_page_identity_deep_runtime.py 2>&1 )"; \
	targets_line="$$(echo "$$runtime_output" | grep '^FRONTEND_PAGE_IDENTITY_DEEP_TARGETS_JSON=' | tail -1)"; \
	test -n "$$targets_line"; export "$$targets_line"; \
	$(MAKE) --no-print-directory backend.acceptance.up; \
	$(MAKE) --no-print-directory frontend.acceptance.up; \
	trap '$(MAKE) --no-print-directory frontend.acceptance.down; $(MAKE) --no-print-directory backend.acceptance.down' EXIT; \
	$(RUN_ENV) DB_NAME=$(FRONTEND_ACCEPTANCE_DB) SC_ENVIRONMENT=acceptance SC_ALLOW_DEMO_DATA=1 FRONTEND_URL=$${FRONTEND_URL:-http://127.0.0.1:5175} ARTIFACTS_DIR=artifacts/frontend-page-identity-deep FRONTEND_PAGE_IDENTITY_DEEP_TARGETS_JSON="$${FRONTEND_PAGE_IDENTITY_DEEP_TARGETS_JSON}" node scripts/verify/frontend_page_identity_deep_browser.mjs

policy.apply.business_full: guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) POLICY_MODULE=smart_construction_custom DB_NAME=$(DB_NAME) bash scripts/audit/apply_business_full_policy.sh
policy.apply.role_matrix: guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) POLICY_MODULE=smart_construction_custom DB_NAME=$(DB_NAME) bash scripts/audit/apply_role_matrix.sh
	@echo "⚠️  policy.apply.role_matrix finished; restarting Odoo to refresh ACL caches"
	@$(MAKE) restart
smoke.business_full: check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/audit/smoke_business_full.sh
smoke.role_matrix: check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/audit/smoke_role_matrix.sh

policy.ensure.role_surface_demo: guard.prod.forbid check-compose-project check-compose-env
	@set -e; \
	if $(MAKE) --no-print-directory verify.portal.role_surface_preflight.container DB_NAME=$(DB_NAME); then \
	  echo "[policy.ensure.role_surface_demo] already satisfied"; \
	elif [ "$${AUTO_FIX_ROLE_SURFACE_DEMO:-0}" = "1" ]; then \
	  echo "[policy.ensure.role_surface_demo] applying auto-fix for role surface demo baseline"; \
	  $(MAKE) --no-print-directory mod.install MODULE=smart_construction_custom DB_NAME=$(DB_NAME); \
	  $(MAKE) --no-print-directory mod.install MODULE=smart_construction_seed DB_NAME=$(DB_NAME); \
	  $(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/link_existing_demo_user_xmlids.sh; \
	  $(MAKE) --no-print-directory mod.install MODULE=smart_construction_demo DB_NAME=$(DB_NAME); \
	  $(RUN_ENV) DB_NAME=$(DB_NAME) ROLE_SMOKE_PASSWORD="$${ROLE_SMOKE_PASSWORD:-demo}" bash scripts/ops/ensure_role_surface_demo.sh; \
	  $(MAKE) --no-print-directory restart; \
	  $(MAKE) --no-print-directory verify.portal.role_surface_preflight.container DB_NAME=$(DB_NAME); \
	else \
	  echo "[policy.ensure.role_surface_demo] FAIL: role surface demo baseline not satisfied"; \
	  echo "[policy.ensure.role_surface_demo] HINT: re-run with AUTO_FIX_ROLE_SURFACE_DEMO=1"; \
	  echo "[policy.ensure.role_surface_demo] HINT: optional ROLE_SMOKE_PASSWORD=<pwd> to set smoke login password"; \
	  exit 2; \
	fi

verify.portal.role_surface_preflight.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/role_surface_preflight.sh

verify.portal.role_surface_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(MAKE) --no-print-directory verify.portal.role_surface_preflight.container DB_NAME=$(DB_NAME)
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) python3 /mnt/scripts/verify/role_surface_smoke.py"

p2.smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(MAKE) db.policy DB=$(DB_NAME)
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/validate_p2_runtime.sh

p3.smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(MAKE) db.policy DB=$(DB_NAME)
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/validate_p3_runtime.sh

p3.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(MAKE) db.policy DB=$(DB_NAME)
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/validate_p3_audit.sh

codex.preflight:
	@bash scripts/ops/codex_preflight.sh

codex.merge: guard.prod.forbid check-compose-project check-compose-env
	@bash scripts/ops/codex_merge.sh

codex.rollback: guard.prod.forbid
	@bash scripts/ops/codex_rollback.sh

codex.pr.body: guard.prod.forbid
	@bash scripts/ops/codex_pr_body.sh "$(PR_BODY_FILE)" "artifacts/codex/$$(git rev-parse --abbrev-ref HEAD)"

codex.release.note: guard.prod.forbid
	@bash scripts/ops/codex_release_note.sh "docs/ops/releases/README.md"

db.policy:
	@DB=$(DB) bash scripts/ops/check_db_policy.sh

stage.preflight:
	@DB=$(DB_NAME) bash scripts/ops/stage_preflight.sh

stage.run:
	@STAGE=$(STAGE) DB=$(DB_NAME) bash scripts/ops/stage_run.sh

# ------------------ Auth policy (dev-style) ------------------
AUTH_PROJECT ?= sc-backend-odoo-prod
AUTH_DB      ?= sc_prod

ops.auth.dev.apply:
	@./scripts/ops/auth_policy.sh apply -p $(AUTH_PROJECT) -d $(AUTH_DB)

ops.auth.dev.rollback:
	@./scripts/ops/auth_policy.sh rollback -p $(AUTH_PROJECT) -d $(AUTH_DB)

ops.auth.dev.verify:
	@./scripts/ops/auth_policy.sh verify -p $(AUTH_PROJECT) -d $(AUTH_DB)

.PHONY: demo.verify demo.load demo.list demo.load.all demo.load.full demo.load.release demo.install demo.rebuild demo.ci demo.repro demo.full seed.run verify.non_demo_data_contamination audit.project.actions audit.nav.alignment audit.nav.role_diff
demo.verify: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) SCENARIO=$(SCENARIO) STEP=$(STEP) bash scripts/demo/verify.sh

demo.load: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) SCENARIO=$(SCENARIO) STEP=$(STEP) bash scripts/demo/load.sh

demo.list: check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/demo/list.sh

demo.load.all: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/demo/load_all.sh

demo.load.full: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/demo/load_full.sh

demo.load.release: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/demo/load_release.sh

demo.install: guard.prod.forbid check-compose-project check-compose-env
	@echo "[demo.install] db=$(DB_NAME)"
	@test -n "$(DB_NAME)" || (echo "ERROR: DB_NAME is required" && exit 2)
	@$(MAKE) mod.install MODULE=smart_construction_demo DB_NAME=$(DB_NAME)

demo.rebuild: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/demo/rebuild.sh

demo.ci: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/demo/ci.sh

demo.repro: guard.prod.forbid check-compose-project check-compose-env
	@$(MAKE) demo.reset DB=$(DB_NAME)
	@$(MAKE) demo.load DB=$(DB_NAME) SCENARIO=s00_min_path
	@$(MAKE) demo.verify DB=$(DB_NAME)

demo.full: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/demo/full.sh

seed.run: check-compose-project check-compose-env
	@$(RUN_ENV) STEPS=$(STEPS) bash scripts/seed/run.sh

.PHONY: verify.non_demo_data_contamination
verify.non_demo_data_contamination: check-compose-project check-compose-env
	@mkdir -p artifacts/backend
	@status=0; \
	$(RUN_ENV) \
		NON_DEMO_DATA_CONTAMINATION_GUARD_JSON=/tmp/non_demo_data_contamination_guard.json \
		NON_DEMO_DATA_CONTAMINATION_GUARD_MD=/tmp/non_demo_data_contamination_guard.md \
		DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/non_demo_data_contamination_guard.py || status=$$?; \
	$(RUN_ENV) $(COMPOSE_BASE) cp $(ODOO_SERVICE):/tmp/non_demo_data_contamination_guard.json artifacts/backend/non_demo_data_contamination_guard.json >/dev/null 2>&1 || true; \
	$(RUN_ENV) $(COMPOSE_BASE) cp $(ODOO_SERVICE):/tmp/non_demo_data_contamination_guard.md artifacts/backend/non_demo_data_contamination_guard.md >/dev/null 2>&1 || true; \
	schema_status=0; python3 scripts/verify/non_demo_data_contamination_guard_schema_guard.py || schema_status=$$?; \
	if [ "$$status" -eq 0 ]; then status=$$schema_status; fi; \
	exit $$status

audit.project.actions: guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) OUT=$(OUT) bash scripts/ops/audit_project_actions.sh

audit.nav.alignment: guard.prod.forbid check-compose-project check-compose-env
	@ENABLE_SUGGESTIONS=1 $(MAKE) --no-print-directory audit.project.actions DB_NAME=$(DB_NAME)
	@$(MAKE) --no-print-directory verify.menu.scene_resolve.container DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD)
	@python3 scripts/audit/nav_alignment_report.py

audit.nav.role_diff: guard.prod.forbid check-compose-project check-compose-env
	@$(MAKE) --no-print-directory verify.portal.role_surface_preflight.container DB_NAME=$(DB_NAME)
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) ROOT_XMLID=$(ROOT_XMLID) ROLE_OWNER_LOGIN=$(or $(ROLE_OWNER_LOGIN),demo_role_owner) ROLE_OWNER_PASSWORD=$(or $(ROLE_OWNER_PASSWORD),demo) ROLE_PM_LOGIN=$(or $(ROLE_PM_LOGIN),demo_role_pm) ROLE_PM_PASSWORD=$(or $(ROLE_PM_PASSWORD),demo) ROLE_FINANCE_LOGIN=$(or $(ROLE_FINANCE_LOGIN),demo_role_finance) ROLE_FINANCE_PASSWORD=$(or $(ROLE_FINANCE_PASSWORD),demo) ROLE_EXECUTIVE_LOGIN=$(or $(ROLE_EXECUTIVE_LOGIN),demo_role_executive) ROLE_EXECUTIVE_PASSWORD=$(or $(ROLE_EXECUTIVE_PASSWORD),demo) python3 /mnt/scripts/audit/role_nav_diff.py"

.PHONY: prod.upgrade.core
prod.upgrade.core: guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) MODULE=smart_construction_core DB_NAME=$(DB_NAME) bash scripts/mod/upgrade.sh
	@$(MAKE) restart

.PHONY: audit.pull
audit.pull:
	@DB=$(DB_NAME) bash scripts/audit/pull.sh

.PHONY: audit.boundary
audit.boundary:
	@bash scripts/audit/boundary_lint.sh

gate.full: guard.codex.fast.noheavy guard.prod.forbid check-compose-project check-compose-env
	@if ! docker info >/dev/null 2>&1; then \
	  echo "❌ docker is required for gate.full (containers not available)"; \
	  echo "   Fix: start docker or run with SC_GATE_STRICT=0 for local-only checks."; \
	  exit 2; \
	fi
	@if [ "$(ENV)" = "dev" ] || [ "$(ENV)" = "test" ] || [ "$(ENV)" = "local" ] || [ "$(CONTRACT_PREFLIGHT_CONTINUE_FROM_FAILURE)" = "1" ]; then \
	  $(MAKE) --no-print-directory verify.contract.preflight.resume; \
	else \
	  $(MAKE) --no-print-directory verify.contract.preflight; \
	fi
	@$(MAKE) --no-print-directory verify.frontend.home_suggestion_semantics.guard
	@$(MAKE) --no-print-directory verify.frontend.page_contract_boundary.guard
	@KEEP_TEST_CONTAINER=1 $(MAKE) test TEST_TAGS=sc_gate BD=$(DB_NAME)
	@$(MAKE) verify.demo BD=$(DB_NAME)
	@$(MAKE) --no-print-directory gate.scene.r3.runtime.strict
	@if [ "$(SC_GATE_STRICT)" != "0" ]; then \
	  $(MAKE) verify.menu.scene_resolve.container DB_NAME=$(DB_NAME); \
	  $(MAKE) verify.menu.scene_resolve.summary; \
	  $(MAKE) verify.menu.navigation_snapshot.container DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD); \
	  $(MAKE) verify.portal.scene_warnings_guard.container DB_NAME=$(DB_NAME); \
	  $(MAKE) verify.portal.scene_warnings_limit.container DB_NAME=$(DB_NAME); \
	  $(MAKE) verify.portal.act_url_missing_scene_report.container DB_NAME=$(DB_NAME); \
	  $(MAKE) verify.portal.cross_stack_contract_smoke.container DB_NAME=$(DB_NAME); \
	  $(MAKE) verify.portal.my_work_smoke.container DB_NAME=$(DB_NAME); \
	  $(MAKE) verify.portal.scene_observability_gate_smoke.container DB_NAME=$(DB_NAME); \
	  if [ "$(SC_SCENE_OBS_STRICT)" = "1" ]; then \
	    $(MAKE) verify.portal.scene_observability_strict.container DB_NAME=$(DB_NAME); \
	  else \
	    echo "[gate.full] SC_SCENE_OBS_STRICT=0: skip strict scene observability checks"; \
	  fi; \
	else \
	  echo "[gate.full] SC_GATE_STRICT=0: skip menu/act_url guard checks"; \
	fi
	@$(MAKE) verify.phase_9_8.gate_summary
	@$(MAKE) audit.pull DB_NAME=$(DB_NAME)
