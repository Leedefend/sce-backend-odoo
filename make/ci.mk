# ======================================================
# ==================== CI ==============================
# ======================================================
.PHONY: ci.preflight.contract ci.scene.delivery.readiness ci.gate ci.smoke ci.full ci.repro \
	test-install-gate test-upgrade-gate \
	ci.clean ci.ps ci.logs gate.boundary

.PHONY: refresh.delivery.readiness.scoreboard
refresh.delivery.readiness.scoreboard: guard.prod.forbid
	@python3 scripts/verify/delivery_readiness_scoreboard_refresh.py

# CI preflight: fail-fast on contract drift before heavier test suites.
ci.preflight.contract: guard.prod.forbid
	@$(MAKE) --no-print-directory verify.contract.preflight
	@$(MAKE) --no-print-directory verify.frontend.home_suggestion_semantics.guard
	@$(MAKE) --no-print-directory verify.frontend.page_contract_boundary.guard

ci.scene.delivery.readiness: guard.prod.forbid
	@CI_SCENE_DELIVERY_PROFILE=$${CI_SCENE_DELIVERY_PROFILE:-strict}; \
	 echo "[ci.scene.delivery.readiness] profile=$$CI_SCENE_DELIVERY_PROFILE"; \
	 if [ "$$CI_SCENE_DELIVERY_PROFILE" = "restricted" ]; then \
	   if SC_SCENE_READY_CONSUMPTION_TREND_REQUIRE_LIVE=0 \
	      SC_SCENE_ACTION_SURFACE_STRATEGY_PAYLOAD_REQUIRE_LIVE=0 \
	      SC_SCENE_ACTION_STRATEGY_LIVE_MATRIX_REQUIRE_LIVE=0 \
	      $(MAKE) --no-print-directory verify.scene.delivery.readiness.role_company_matrix; then \
	     python3 scripts/verify/delivery_readiness_scoreboard_refresh.py --profile $$CI_SCENE_DELIVERY_PROFILE --status PASS; \
	     exit 0; \
	   fi; \
	 else \
	   if $(MAKE) --no-print-directory verify.scene.delivery.readiness.role_company_matrix; then \
	     python3 scripts/verify/delivery_readiness_scoreboard_refresh.py --profile $$CI_SCENE_DELIVERY_PROFILE --status PASS; \
	     exit 0; \
	   fi; \
	 fi; \
	 python3 scripts/verify/delivery_readiness_scoreboard_refresh.py --profile $$CI_SCENE_DELIVERY_PROFILE --status FAIL; \
	 python3 scripts/verify/scene_delivery_failure_brief.py; \
	 python3 scripts/verify/scene_delivery_failure_brief_summary.py; \
	 exit 1

# 只跑守门：权限/绕过（最快定位安全回归）
ci.gate: guard.prod.forbid ci.preflight.contract
	@$(RUN_ENV) TEST_TAGS="sc_gate,sc_perm" bash scripts/ci/run_ci.sh

# 冒烟：基础链路 + 守门
ci.smoke: guard.prod.forbid ci.preflight.contract
	@$(RUN_ENV) TEST_TAGS="sc_smoke,sc_gate" bash scripts/ci/run_ci.sh

# 全量：用 TEST_TAGS（默认 sc_smoke,sc_gate，也可你自定义覆盖）
ci.full: guard.prod.forbid ci.preflight.contract
	@$(RUN_ENV) bash scripts/ci/run_ci.sh

# 复现：不清理 artifacts，保留现场
ci.repro: guard.prod.forbid ci.preflight.contract
	@$(RUN_ENV) CI_ARTIFACT_PURGE=0 bash scripts/ci/run_ci.sh

test-install-gate:
	@$(RUN_ENV) bash scripts/ci/install_gate.sh
test-upgrade-gate:
	@$(RUN_ENV) bash scripts/ci/upgrade_gate.sh

ci.clean: guard.prod.forbid
	@$(RUN_ENV) bash scripts/ci/ci_clean.sh
ci.ps: guard.prod.forbid
	@$(RUN_ENV) bash scripts/ci/ci_ps.sh
ci.logs: guard.prod.forbid
	@$(RUN_ENV) bash scripts/ci/ci_logs.sh

gate.boundary: guard.prod.forbid check-compose-project check-compose-env
	@$(MAKE) audit.boundary.smart_core

# ======================================================
# ==================== Diagnostics ======================
# ======================================================
.PHONY: diag.compose verify.ops gate.audit ci.gate.tp08 audit.boundary.smart_core audit.boundary.smart_core.ci
diag.compose: check-compose-env
	@echo "=== base ==="
	@$(COMPOSE_BASE) config | sed -n '/^services:/,/^volumes:/p' | sed -n '1,200p'
	@echo "=== base+ci ==="
	@$(COMPOSE_CI) config | sed -n '/^services:/,/^volumes:/p' | sed -n '1,200p'
	@echo "=== base+testdeps ==="
	@out="$$( $(COMPOSE_TESTDEPS) config 2>&1 )"; \
	status=$$?; \
	echo "$$out" | sed -n '/^services:/,/^volumes:/p' | sed -n '1,200p'; \
	echo "=== base+testdeps err ==="; \
	if [ $$status -ne 0 ]; then echo "$$out" | sed -n '1,120p'; fi

verify.ops: guard.prod.forbid check-compose-project check-compose-env
	@echo "== verify.ops =="
	@echo "[1] docker daemon"
	@docker info >/dev/null && echo "OK docker daemon" || (echo "FAIL docker daemon" && exit 2)
	@echo "[2] compose project"
	@$(COMPOSE_BASE) ps
	@echo "[3] odoo recreate"
	@$(MAKE) odoo.recreate
	@echo "[4] module upgrade smoke"
	@$(MAKE) mod.upgrade MODULE=$(MODULE)
	@echo "🎉 verify.ops PASSED"

gate.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/ci/gate_audit.sh

# ======================================================
# ==================== Boundary Audit ==================
# ======================================================
audit.boundary.smart_core: guard.prod.forbid
	@$(RUN_ENV) python3 scripts/audit/boundary_audit_smart_core.py \
		--root "$(ROOT_DIR)" \
		--scan-dir "addons/smart_core" \
		--json-out "$(BOUNDARY_AUDIT_JSON_OUT)" \
		--md-out "$(BOUNDARY_AUDIT_MD_OUT)" \
		--allowlist "scripts/audit/boundary_allowlist.txt" \
		--generated-at "$(BOUNDARY_AUDIT_GENERATED_AT)" \
		--fail-on-reverse-deps

audit.boundary.smart_core.ci: guard.prod.forbid
	@$(MAKE) --no-print-directory audit.boundary.smart_core \
		BOUNDARY_AUDIT_JSON_OUT=artifacts/ci/boundary_audit/smart_core_hits.json \
		BOUNDARY_AUDIT_MD_OUT=artifacts/ci/boundary_audit/smart_core_hits.md \
		BOUNDARY_AUDIT_GENERATED_AT=ci-artifact

ci.gate.tp08: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/ci/gate_audit_tp08.sh

# ======================================================
# ==================== Continue CLI ====================
# ======================================================
# Continue CLI 集成
# 注意: `continue` 是 bash 内置关键字，真正的 CLI 是 `cn`
# 
# 使用方式:
#   make cn.p PROMPT="任务描述"          # 无闪烁批处理模式
#   make cn.tui                          # 交互式 TUI 模式（可能闪烁）
#   echo "任务" | make cn.p.stdin        # 管道输入模式

# 项目配置路径
CN_PROJECT_CONFIG ?= $(ROOT_DIR)/tools/continue/config/continue-deepseek.json

# Continue CLI 脚本路径
CN_PRINT_SCRIPT ?= scripts/ops/cn_print.sh

# Continue CLI 超时设置（秒）
CN_TIMEOUT ?= 180

# 验证提示参数
guard.cn.prompt:
	@if [ -z "$(PROMPT)" ] && [ -t 0 ]; then \
		echo "❌ 错误: 需要提供提示 (PROMPT=... 或通过管道输入)"; \
		echo "用法: make cn.p PROMPT=\"任务描述\""; \
		echo "用法: echo \"任务\" | make cn.p.stdin"; \
		exit 2; \
	fi

# 无闪烁批处理模式
cn.p: guard.cn.prompt
	@echo "▶ 执行 Continue 批处理任务 (无闪烁模式)"
	@echo "提示: $(PROMPT)"
	@echo "配置: $(CN_PROJECT_CONFIG)"
	@echo "超时: $(CN_TIMEOUT)秒"
	@CN_CONFIG="$(CN_PROJECT_CONFIG)" CN_TIMEOUT="$(CN_TIMEOUT)" bash "$(CN_PRINT_SCRIPT)" "$(PROMPT)"

# 管道输入模式
cn.p.stdin: guard.cn.prompt
	@echo "▶ 执行 Continue 批处理任务 (管道输入模式)"
	@echo "配置: $(CN_PROJECT_CONFIG)"
	@echo "超时: $(CN_TIMEOUT)秒"
	@CN_CONFIG="$(CN_PROJECT_CONFIG)" CN_TIMEOUT="$(CN_TIMEOUT)" bash "$(CN_PRINT_SCRIPT)"

# 交互式 TUI 模式 (可能闪烁)
cn.tui:
	@echo "⚠ 警告: 交互式 TUI 模式可能导致屏幕闪烁"
	@echo "提示: 按 Ctrl+C 退出"
	@if [ -f "$(CN_PROJECT_CONFIG)" ]; then \
		cn --config "$(CN_PROJECT_CONFIG)"; \
	else \
		cn; \
	fi

# 测试 Continue CLI 连接
cn.test:
	@echo "▶ 测试 Continue CLI 连接"
	@if command -v cn >/dev/null 2>&1; then \
		echo "✅ Continue CLI 已安装"; \
		cn --version || echo "⚠ 无法获取版本信息"; \
	else \
		echo "❌ Continue CLI 未安装"; \
		echo "安装: npm install -g @continuedev/cli"; \
		exit 1; \
	fi
	@echo ""
	@echo "▶ 测试主链路配置（与 cn.p 使用相同逻辑）"
	@echo "  配置选择逻辑验证..."
	@# 模拟 cn_print.sh 的配置选择逻辑
	@if [ -f "$(HOME)/.continue/config.json" ]; then \
		echo "✅ 使用用户 JSON 配置: $(HOME)/.continue/config.json"; \
		CONFIG_SOURCE="用户JSON配置"; \
	elif [ -f "$(HOME)/.continue/config.yaml" ]; then \
		echo "✅ 使用用户 YAML 配置: $(HOME)/.continue/config.yaml"; \
		CONFIG_SOURCE="用户YAML配置"; \
	elif [ -f "$(CN_PROJECT_CONFIG)" ]; then \
		echo "⚠ 使用项目配置（用户配置不存在）: $(CN_PROJECT_CONFIG)"; \
		CONFIG_SOURCE="项目配置"; \
	else \
		echo "❌ 错误: 未找到 Continue 配置文件"; \
		exit 1; \
	fi
	@echo "✅ 配置选择逻辑正常（与 cn.p 相同）"
	@echo ""
	@echo "▶ 配置源信息"
	@if [ -f "$(HOME)/.continue/config.json" ]; then \
		echo "✅ 用户 JSON 配置存在: $(HOME)/.continue/config.json"; \
	elif [ -f "$(HOME)/.continue/config.yaml" ]; then \
		echo "✅ 用户 YAML 配置存在: $(HOME)/.continue/config.yaml"; \
	else \
		echo "⚠ 用户配置不存在"; \
	fi
	@if [ -f "$(CN_PROJECT_CONFIG)" ]; then \
		echo "✅ 项目配置存在: $(CN_PROJECT_CONFIG)"; \
	else \
		echo "⚠ 项目配置不存在"; \
	fi

# ======================================================
# ==================== Continue Audit ===================
# ======================================================
# 文档字符串审计
CN_AUDIT_MODULE ?= addons/smart_construction_core
CN_AUDIT_OUTDIR ?= artifacts/continue

# 文档字符串审计主任务
cn.audit.docstrings:
	@echo "▶ 开始文档字符串审计"
	@echo "模块: $(CN_AUDIT_MODULE)"
	@echo "输出目录: $(CN_AUDIT_OUTDIR)"
	@echo "扫描器: tools/continue/auditors/docstrings_scanner.py"
	@mkdir -p "$(CN_AUDIT_OUTDIR)"
	@python3 tools/continue/auditors/docstrings_scanner.py "$(CN_AUDIT_MODULE)" "$(CN_AUDIT_OUTDIR)"
	@echo ""
	@echo "📊 审计报告:"
	@echo "  - $(CN_AUDIT_OUTDIR)/audit_docstrings.md (人读报告)"
	@echo "  - $(CN_AUDIT_OUTDIR)/audit_docstrings.json (机器数据)"
	@echo ""
	@echo "✅ 文档字符串审计完成"

# 文档字符串审计测试（小样本）
cn.audit.docstrings.test:
	@echo "▶ 测试文档字符串审计（小样本）"
	@echo "测试目录: addons/smart_construction_core/controllers"
	@echo "输出目录: $(CN_AUDIT_OUTDIR)"
	@mkdir -p "$(CN_AUDIT_OUTDIR)"
	@python3 tools/continue/auditors/docstrings_scanner.py "addons/smart_construction_core/controllers" "$(CN_AUDIT_OUTDIR)"
	@echo ""
	@echo "✅ 测试审计完成（仅扫描controllers目录）"

# 清理审计产物
cn.audit.docstrings.clean:
	@echo "▶ 清理审计产物"
	@rm -rf "$(CN_AUDIT_OUTDIR)/audit_docstrings.md" "$(CN_AUDIT_OUTDIR)/audit_docstrings.json" 2>/dev/null || true
	@echo "✅ 清理完成"

# ======================================================
# ==================== Continue Help ====================
# ======================================================
# 显示帮助信息
cn.help:
	@echo "Continue CLI 集成帮助:"
	@echo ""
	@echo "无闪烁批处理模式:"
	@echo "  make cn.p PROMPT=\"任务描述\""
	@echo "  示例: make cn.p PROMPT=\"分析代码问题\""
	@echo ""
	@echo "管道输入模式:"
	@echo "  echo \"任务描述\" | make cn.p.stdin"
	@echo "  示例: echo \"修复bug\" | make cn.p.stdin"
	@echo ""
	@echo "交互式 TUI 模式 (可能闪烁):"
	@echo "  make cn.tui"
	@echo ""
	@echo "测试连接:"
	@echo "  make cn.test"
	@echo ""
	@echo "审计功能:"
	@echo "  make cn.audit.docstrings          # 文档字符串审计"
	@echo "  make cn.audit.docstrings.test     # 测试审计（小样本）"
	@echo "  make cn.audit.docstrings.clean    # 清理审计产物"
	@echo ""
	@echo "配置路径: $(CN_PROJECT_CONFIG)"
	@echo "脚本路径: $(CN_PRINT_SCRIPT)"
	@echo "审计模块: $(CN_AUDIT_MODULE)"
	@echo "审计输出: $(CN_AUDIT_OUTDIR)"
	@echo ""
	@echo "注意:"
	@echo "  - 闪烁问题由交互式 TUI 引起，批处理模式可避免"
	@echo "  - 确保已安装 Continue CLI: npm install -g @continuedev/cli"

.PHONY: cn.p cn.p.stdin cn.tui cn.test cn.help guard.cn.prompt

.PHONY: verify.native_view.semantic_page.shape
verify.native_view.semantic_page.shape: guard.prod.forbid
	@python3 scripts/verify/native_view_semantic_page_shape_guard.py --dir docs/contract/snapshots/native_view --output artifacts/backend/native_view_semantic_page_shape_guard.json

.PHONY: verify.native_view.semantic_page.schema
verify.native_view.semantic_page.schema: guard.prod.forbid
	@python3 scripts/verify/native_view_semantic_page_schema_guard.py --schema docs/architecture/native_view_contract/semantic_page_contract_shape_v1.schema.json --dir docs/contract/snapshots/native_view --output artifacts/backend/native_view_semantic_page_schema_guard.json

.PHONY: verify.native_view.semantic_page
verify.native_view.semantic_page: verify.native_view.semantic_page.shape verify.native_view.semantic_page.schema

.PHONY: verify.native_view.coverage.report
verify.native_view.coverage.report: guard.prod.forbid verify.native_view.semantic_page
	@python3 scripts/verify/native_view_coverage_report.py

.PHONY: verify.native_view.samples.compare
verify.native_view.samples.compare: guard.prod.forbid verify.native_view.semantic_page
	@python3 scripts/verify/native_view_sample_compare_report.py

.PHONY: verify.native_view.ecosystem.readiness
verify.native_view.ecosystem.readiness: guard.prod.forbid
	@python3 scripts/verify/native_view_ecosystem_readiness_report.py

.PHONY: verify.unified_page_contract.v2.schema
verify.unified_page_contract.v2.schema: guard.prod.forbid
	@python3 scripts/verify/unified_page_contract_v2_schema_guard.py --schema docs/architecture/unified_page_contract_v2/unified_page_contract_v2.schema.json --enum-registry docs/architecture/unified_page_contract_v2/enum_registry.json --examples docs/architecture/unified_page_contract_v2/examples

.PHONY: verify.unified_page_contract.v2.guard_inventory
verify.unified_page_contract.v2.guard_inventory: guard.prod.forbid
	@python3 -m py_compile scripts/verify/unified_page_contract_v2_guard_inventory.py
	@python3 scripts/verify/unified_page_contract_v2_guard_inventory.py

.PHONY: verify.unified_page_contract.v2.assembler
verify.unified_page_contract.v2.assembler: guard.prod.forbid
	@python3 -m py_compile addons/smart_core/core/unified_page_contract_v2_assembler.py scripts/verify/unified_page_contract_v2_assembler_guard.py
	@python3 scripts/verify/unified_page_contract_v2_assembler_guard.py --fixtures docs/architecture/unified_page_contract_v2/fixtures --snapshot docs/architecture/unified_page_contract_v2/snapshots/assembler_mapping_snapshot_v1.json --enum-registry docs/architecture/unified_page_contract_v2/enum_registry.json

.PHONY: verify.unified_page_contract.v2.status
verify.unified_page_contract.v2.status: guard.prod.forbid
	@python3 -m py_compile addons/smart_core/core/unified_page_contract_v2_status.py scripts/verify/unified_page_contract_v2_status_guard.py
	@python3 scripts/verify/unified_page_contract_v2_status_guard.py --fixture docs/architecture/unified_page_contract_v2/fixtures/status_contract_source.json --snapshot docs/architecture/unified_page_contract_v2/snapshots/status_contract_snapshot_v1.json --enum-registry docs/architecture/unified_page_contract_v2/enum_registry.json

.PHONY: verify.unified_page_contract.v2.action
verify.unified_page_contract.v2.action: guard.prod.forbid
	@python3 -m py_compile addons/smart_core/core/unified_page_contract_v2_action.py scripts/verify/unified_page_contract_v2_action_guard.py
	@python3 scripts/verify/unified_page_contract_v2_action_guard.py --fixture docs/architecture/unified_page_contract_v2/fixtures/action_contract_source.json --patch-fixture docs/architecture/unified_page_contract_v2/fixtures/action_patch_source.json --snapshot docs/architecture/unified_page_contract_v2/snapshots/action_contract_snapshot_v1.json --enum-registry docs/architecture/unified_page_contract_v2/enum_registry.json

.PHONY: verify.unified_page_contract.v2.data
verify.unified_page_contract.v2.data: guard.prod.forbid
	@python3 -m py_compile addons/smart_core/core/unified_page_contract_v2_data.py scripts/verify/unified_page_contract_v2_data_guard.py
	@python3 scripts/verify/unified_page_contract_v2_data_guard.py --fixture docs/architecture/unified_page_contract_v2/fixtures/data_contract_source.json --snapshot docs/architecture/unified_page_contract_v2/snapshots/data_contract_snapshot_v1.json --schema docs/architecture/unified_page_contract_v2/unified_page_contract_v2.schema.json --enum-registry docs/architecture/unified_page_contract_v2/enum_registry.json

.PHONY: verify.unified_page_contract.v2.runtime
verify.unified_page_contract.v2.runtime: guard.prod.forbid
	@python3 -m py_compile addons/smart_core/core/unified_page_contract_v2_runtime.py scripts/verify/unified_page_contract_v2_runtime_guard.py addons/smart_core/tests/test_unified_page_contract_v2_runtime.py addons/smart_core/tests/test_unified_page_contract_v2_mobile_compact.py
	@python3 addons/smart_core/tests/test_unified_page_contract_v2_runtime.py
	@python3 addons/smart_core/tests/test_unified_page_contract_v2_mobile_compact.py
	@python3 scripts/verify/unified_page_contract_v2_runtime_guard.py --fixture docs/architecture/unified_page_contract_v2/fixtures/runtime_contract_source.json --snapshot docs/architecture/unified_page_contract_v2/snapshots/runtime_contract_snapshot_v1.json --schema docs/architecture/unified_page_contract_v2/unified_page_contract_v2.schema.json --enum-registry docs/architecture/unified_page_contract_v2/enum_registry.json

.PHONY: verify.unified_page_contract.v2.client
verify.unified_page_contract.v2.client: guard.prod.forbid
	@python3 -m py_compile addons/smart_core/core/unified_page_contract_v2_client.py scripts/verify/unified_page_contract_v2_client_guard.py
	@python3 scripts/verify/unified_page_contract_v2_client_guard.py --fixture docs/architecture/unified_page_contract_v2/examples/form_project.json --snapshot docs/architecture/unified_page_contract_v2/snapshots/client_trimming_snapshot_v1.json --enum-registry docs/architecture/unified_page_contract_v2/enum_registry.json

.PHONY: verify.unified_page_contract.v2.intent
verify.unified_page_contract.v2.intent: guard.prod.forbid
	@python3 -m py_compile scripts/verify/unified_page_contract_v2_intent_guard.py
	@python3 scripts/verify/unified_page_contract_v2_intent_guard.py

.PHONY: verify.unified_page_contract.v2.harmony_h5_compile_acceptance.host
verify.unified_page_contract.v2.harmony_h5_compile_acceptance.host: guard.prod.forbid
	@python3 scripts/verify/unified_page_contract_v2_harmony_h5_compile_acceptance_guard.py --report artifacts/backend/unified_page_contract_v2_harmony_h5_compile_acceptance.json --execute

.PHONY: verify.unified_page_contract.v2.regression_audit.host
verify.unified_page_contract.v2.regression_audit.host: guard.prod.forbid
	@python3 -m py_compile scripts/verify/unified_page_contract_v2_regression_audit.py
	@python3 scripts/verify/unified_page_contract_v2_regression_audit.py

.PHONY: verify.unified_page_contract.v2.web_consumer
verify.unified_page_contract.v2.web_consumer: guard.prod.forbid
	@python3 -m py_compile scripts/verify/unified_page_contract_v2_web_consumer_guard.py scripts/verify/web_unified_page_contract_v2_guard.py
	@python3 scripts/verify/unified_page_contract_v2_web_consumer_guard.py
	@python3 scripts/verify/web_unified_page_contract_v2_guard.py

.PHONY: verify.unified_page_contract.v2.web_architecture
verify.unified_page_contract.v2.web_architecture: guard.prod.forbid
	@python3 scripts/verify/web_contract_v2_frontend_architecture_guard.py

.PHONY: verify.unified_page_contract.v2.stable_projection
verify.unified_page_contract.v2.stable_projection: guard.prod.forbid
	@python3 -m py_compile scripts/verify/ui_contract_v2_contract_boundary_guard.py scripts/verify/frontend_v2_policy_projection_guard.py
	@python3 scripts/verify/ui_contract_v2_contract_boundary_guard.py
	@python3 scripts/verify/frontend_v2_policy_projection_guard.py

.PHONY: verify.unified_page_contract.v2.frontend_static
verify.unified_page_contract.v2.frontend_static: verify.frontend.typecheck.strict verify.frontend.build

.PHONY: verify.unified_page_contract.v2.web_visual_acceptance.host
verify.unified_page_contract.v2.web_visual_acceptance.host: guard.prod.forbid
	@node scripts/verify/unified_page_contract_v2_web_visual_acceptance.js

.PHONY: verify.unified_page_contract.v2.web_form_shadow_browser.host
verify.unified_page_contract.v2.web_form_shadow_browser.host: guard.prod.forbid
	@node scripts/verify/web_contract_v2_form_shadow_browser_smoke.js

.PHONY: audit.workflow_state.inventory
audit.workflow_state.inventory: guard.prod.forbid
	@mkdir -p "$$(dirname "$(WORKFLOW_CONTRACT_INVENTORY_OUT)")"
	@$(RUN_ENV) DB_NAME="$${DB_NAME:-$(WORKFLOW_CONTRACT_DB_NAME)}" bash scripts/ops/odoo_shell_exec.sh < scripts/audit/workflow_state_inventory.py > "$(WORKFLOW_CONTRACT_INVENTORY_OUT)"

.PHONY: verify.workflow_contract.backend
verify.workflow_contract.backend: guard.prod.forbid audit.workflow_state.inventory
	@python3 -m py_compile addons/smart_construction_core/models/support/workflow_contract_service.py addons/smart_construction_core/tests/test_workflow_contract_backend.py addons/smart_construction_core/tests/test_user_feedback_business_views.py scripts/audit/workflow_state_inventory.py scripts/verify/workflow_inventory_profile_method_guard.py scripts/verify/workflow_contract_custom_coverage_guard.py
	@python3 scripts/verify/workflow_inventory_profile_method_guard.py
	@python3 scripts/verify/workflow_contract_custom_coverage_guard.py
	@DOCS_MOUNT_HOST=./docs DOCS_MOUNT_CONT=/mnt/docs ADDONS_EXTERNAL_MOUNT=/mnt/addons_external/oca_server_ux DB_NAME="$${DB_NAME:-$(WORKFLOW_CONTRACT_DB_NAME)}" MODULE=smart_construction_core TEST_TAGS='/smart_construction_core:TestWorkflowContractBackend' bash scripts/test/test_safe.sh
	@DOCS_MOUNT_HOST=./docs DOCS_MOUNT_CONT=/mnt/docs ADDONS_EXTERNAL_MOUNT=/mnt/addons_external/oca_server_ux DB_NAME="$${DB_NAME:-$(WORKFLOW_CONTRACT_DB_NAME)}" MODULE=smart_construction_core TEST_TAGS='/smart_construction_core:TestUserFeedbackBusinessViews.test_deduction_registration_action_creates_deduction_bill_lines' bash scripts/test/test_safe.sh

.PHONY: verify.workflow_contract.browser.syntax
verify.workflow_contract.browser.syntax: guard.prod.forbid
	@node --check scripts/verify/workflow_evidence_gate_browser_acceptance.js
	@node --check scripts/verify/workflow_create_statusbar_browser_acceptance.js

.PHONY: verify.workflow_contract.browser.expense_claim.host
verify.workflow_contract.browser.expense_claim.host: guard.prod.forbid verify.workflow_contract.browser.syntax
	@FRONTEND_URL="$${FRONTEND_URL:-$(WORKFLOW_CONTRACT_FRONTEND_URL)}" DB_NAME="$${DB_NAME:-$(WORKFLOW_CONTRACT_DB_NAME)}" MODEL=sc.expense.claim RECORD_ID="$(WORKFLOW_CONTRACT_EXPENSE_RECORD_ID)" EXPECTED_REASON_CODE=DEDUCTION_BILL_MISSING_LINES UNIQUE_BUTTON_PATTERN='^提交审批$$' ARTIFACTS_DIR=artifacts/workflow-evidence-gate-browser-workflow-contract-required node scripts/verify/workflow_evidence_gate_browser_acceptance.js

.PHONY: verify.workflow_contract.browser.contract_close.host
verify.workflow_contract.browser.contract_close.host: guard.prod.forbid verify.workflow_contract.browser.syntax
	@FRONTEND_URL="$${FRONTEND_URL:-$(WORKFLOW_CONTRACT_FRONTEND_URL)}" DB_NAME="$${DB_NAME:-$(WORKFLOW_CONTRACT_DB_NAME)}" MODEL=construction.contract RECORD_ID="$(WORKFLOW_CONTRACT_CLOSE_RECORD_ID)" EXPECTED_TEXT='无合同明细的合同不可关闭，请补充明细。' EXPECTED_REASON_CODE=CONTRACT_MISSING_LINES_FOR_CLOSE TARGET_BUTTON_PATTERN='完成' TARGET_BUTTON_LABEL='完成' UNIQUE_BUTTON_PATTERN='^完成$$' FORBIDDEN_BUTTON_PATTERN='提交审批|审批通过|审批驳回|重置为草稿' ARTIFACTS_DIR=artifacts/workflow-evidence-gate-browser-contract-close-workflow-contract-required node scripts/verify/workflow_evidence_gate_browser_acceptance.js

.PHONY: verify.workflow_contract.browser.create_statusbar.host
verify.workflow_contract.browser.create_statusbar.host: guard.prod.forbid verify.workflow_contract.browser.syntax
	@FRONTEND_URL="$${FRONTEND_URL:-$(WORKFLOW_CONTRACT_FRONTEND_URL)}" DB_NAME="$${DB_NAME:-$(WORKFLOW_CONTRACT_DB_NAME)}" ARTIFACTS_DIR=artifacts/workflow-create-statusbar-browser node scripts/verify/workflow_create_statusbar_browser_acceptance.js

.PHONY: verify.workflow_contract.browser.host
verify.workflow_contract.browser.host: verify.workflow_contract.browser.expense_claim.host verify.workflow_contract.browser.contract_close.host verify.workflow_contract.browser.create_statusbar.host

.PHONY: verify.workflow_contract.frontend
verify.workflow_contract.frontend: verify.frontend.typecheck.strict verify.unified_page_contract.v2.web_architecture verify.frontend.build
	@python3 -m py_compile scripts/verify/web_unified_page_contract_v2_guard.py
	@python3 scripts/verify/web_unified_page_contract_v2_guard.py

.PHONY: verify.workflow_contract
verify.workflow_contract: verify.workflow_contract.backend verify.workflow_contract.frontend verify.workflow_contract.browser.host

.PHONY: verify.unified_page_contract.v2
verify.unified_page_contract.v2: verify.unified_page_contract.v2.guard_inventory verify.unified_page_contract.v2.schema verify.unified_page_contract.v2.assembler verify.unified_page_contract.v2.status verify.unified_page_contract.v2.action verify.unified_page_contract.v2.data verify.unified_page_contract.v2.runtime verify.unified_page_contract.v2.client verify.unified_page_contract.v2.intent verify.unified_page_contract.v2.web_consumer verify.unified_page_contract.v2.web_architecture verify.unified_page_contract.v2.stable_projection verify.unified_page_contract.v2.frontend_static

.PHONY: verify.unified_page_contract.lite.api_onchange_interface verify.unified_page_contract.lite.api_onchange_intent.container verify.unified_page_contract.lite.startup_negative.container verify.unified_page_contract.lite.load_contract_negative.container verify.unified_page_contract.lite.load_contract_preview_interface verify.unified_page_contract.lite.load_contract_preview_intent.container verify.unified_page_contract.lite.load_contract_preview_matrix.container verify.unified_page_contract.lite.frontend_runtime_negative verify.unified_page_contract.lite.frontend_pilot_implementation verify.unified_page_contract.lite.frontend_pilot_browser.host verify.unified_page_contract.lite.all_tree_browser.host verify.unified_page_contract.lite.all_tree_legacy_browser.host verify.unified_page_contract.lite.all_tree_matrix_browser.host verify.unified_page_contract.lite.all_tree_acceptance_browser.host verify.unified_page_contract.lite.api_onchange_live_scope.container verify.unified_page_contract.lite.load_contract_live_scope.container verify.unified_page_contract.lite.runtime_scope_closure verify.unified_page_contract.lite.phase1_closure verify.unified_page_contract.lite.phase2_candidate_plan verify.unified_page_contract.lite.phase2_load_contract_gate verify.unified_page_contract.lite.phase3_ui_contract_risk verify.unified_page_contract.lite.frontend_pilot_readiness verify.unified_page_contract.lite.contract_freeze_v2_0 verify.unified_page_contract.lite.mainline_absorption verify.unified_page_contract.lite.rollout_switch verify.unified_page_contract.lite.mainline_readiness verify.unified_page_contract.lite.terminal_client_parity verify.unified_page_contract.lite.terminal_coverage_matrix verify.unified_page_contract.lite.terminal_consumer_boundary verify.unified_page_contract.lite.wx_mini_renderer_input_pilot.host verify.unified_page_contract.lite.harmony_h5_renderer_input_pilot.host verify.unified_page_contract.lite.wx_mini_ui_renderer_pilot.host verify.unified_page_contract.lite.harmony_h5_ui_renderer_pilot.host verify.unified_page_contract.lite.wx_mini_page_integration_pilot.host verify.unified_page_contract.lite.harmony_h5_page_integration_pilot.host verify.unified_page_contract.lite.wx_mini_runtime_mount_pilot.host verify.unified_page_contract.lite.harmony_h5_runtime_mount_pilot.host verify.unified_page_contract.lite.wx_mini_compile_pilot.host verify.unified_page_contract.lite.wx_mini_real_compile_pilot.host verify.unified_page_contract.lite.wx_mini_runtime_acceptance_pilot.host verify.unified_page_contract.lite.wx_mini_device_acceptance_pilot.host verify.unified_page_contract.lite.harmony_h5_compile_pilot.host verify.unified_page_contract.lite.harmony_h5_runtime_acceptance_pilot.host verify.unified_page_contract.lite.harmony_h5_device_acceptance_pilot.host verify.unified_page_contract.lite
verify.unified_page_contract.lite.api_onchange_interface: guard.prod.forbid
	@MIGRATION_ARTIFACT_ROOT=/mnt/artifacts/backend DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/unified_page_contract_lite_api_onchange_preview_interface_probe.py

verify.unified_page_contract.lite.api_onchange_intent.container: guard.prod.forbid
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/unified_page_contract_lite_api_onchange_preview_intent_smoke.py"

verify.unified_page_contract.lite.startup_negative.container: guard.prod.forbid
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/unified_page_contract_lite_startup_chain_negative_smoke.py"

verify.unified_page_contract.lite.load_contract_negative.container: guard.prod.forbid
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/unified_page_contract_lite_load_contract_negative_smoke.py"

verify.unified_page_contract.lite.load_contract_preview_interface: guard.prod.forbid
	@MIGRATION_ARTIFACT_ROOT=/mnt/artifacts/backend DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh < scripts/verify/unified_page_contract_lite_load_contract_preview_interface_probe.py

verify.unified_page_contract.lite.load_contract_preview_intent.container: guard.prod.forbid
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/unified_page_contract_lite_load_contract_preview_intent_smoke.py"

verify.unified_page_contract.lite.load_contract_preview_matrix.container: guard.prod.forbid
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) LITE_LOAD_CONTRACT_MATRIX='$(LITE_LOAD_CONTRACT_MATRIX)' python3 /mnt/scripts/verify/unified_page_contract_lite_load_contract_preview_matrix_smoke.py"

verify.unified_page_contract.lite.frontend_runtime_negative: guard.prod.forbid
	@python3 scripts/verify/unified_page_contract_lite_frontend_runtime_negative_guard.py --report artifacts/backend/unified_page_contract_lite_frontend_runtime_negative.json

verify.unified_page_contract.lite.frontend_pilot_implementation: verify.unified_page_contract.lite.frontend_runtime_negative
	@python3 scripts/verify/unified_page_contract_lite_frontend_pilot_implementation_guard.py --makefile Makefile --runtime-negative-report artifacts/backend/unified_page_contract_lite_frontend_runtime_negative.json --report artifacts/backend/unified_page_contract_lite_frontend_pilot_implementation.json

verify.unified_page_contract.lite.frontend_pilot_browser.host: guard.prod.forbid
	@FRONTEND_URL=$${FRONTEND_URL:-http://127.0.0.1:5175} DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) LITE_PILOT_ACTION_ID=$${LITE_PILOT_ACTION_ID:-506} node scripts/verify/unified_page_contract_lite_frontend_pilot_browser_smoke.js

verify.unified_page_contract.lite.all_tree_browser.host: guard.prod.forbid
	@FRONTEND_URL=$${FRONTEND_URL:-http://127.0.0.1:5176} DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) LITE_ALL_TREE_ACTION_IDS=$${LITE_ALL_TREE_ACTION_IDS:-506} node scripts/verify/unified_page_contract_lite_all_tree_browser_smoke.js

verify.unified_page_contract.lite.all_tree_legacy_browser.host: guard.prod.forbid
	@FRONTEND_URL=$${FRONTEND_URL:-http://127.0.0.1:5176} DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) LITE_ALL_TREE_LEGACY_ACTION_ID=$${LITE_ALL_TREE_LEGACY_ACTION_ID:-642} node scripts/verify/unified_page_contract_lite_all_tree_legacy_browser_smoke.js

verify.unified_page_contract.lite.all_tree_matrix_browser.host: guard.prod.forbid
	@FRONTEND_URL=$${FRONTEND_URL:-http://127.0.0.1:5176} API_BASE_URL=$${API_BASE_URL:-http://127.0.0.1:8070} DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) LITE_ALL_TREE_MATRIX_LIMIT=$${LITE_ALL_TREE_MATRIX_LIMIT:-8} node scripts/verify/unified_page_contract_lite_all_tree_matrix_browser_smoke.js

verify.unified_page_contract.lite.all_tree_acceptance_browser.host: verify.unified_page_contract.lite.all_tree_browser.host verify.unified_page_contract.lite.all_tree_legacy_browser.host verify.unified_page_contract.lite.all_tree_matrix_browser.host
	@echo "[OK] verify.unified_page_contract.lite.all_tree_acceptance_browser.host done"

verify.unified_page_contract.lite.api_onchange_live_scope.container: verify.unified_page_contract.lite.api_onchange_interface verify.unified_page_contract.lite.api_onchange_intent.container verify.unified_page_contract.lite.startup_negative.container verify.unified_page_contract.lite.load_contract_negative.container verify.unified_page_contract.lite.frontend_runtime_negative
	@echo "[OK] verify.unified_page_contract.lite.api_onchange_live_scope.container done"

verify.unified_page_contract.lite.load_contract_live_scope.container: verify.unified_page_contract.lite.load_contract_preview_interface verify.unified_page_contract.lite.load_contract_preview_intent.container verify.unified_page_contract.lite.load_contract_preview_matrix.container verify.unified_page_contract.lite.load_contract_negative.container verify.unified_page_contract.lite.startup_negative.container verify.unified_page_contract.lite.frontend_runtime_negative
	@echo "[OK] verify.unified_page_contract.lite.load_contract_live_scope.container done"

verify.unified_page_contract.lite.runtime_scope_closure: guard.prod.forbid
	@python3 scripts/verify/unified_page_contract_lite_runtime_scope_closure_guard.py --matrix docs/architecture/unified_page_contract_lite/integration_validation_matrix_batch_26.md --closure-doc docs/architecture/unified_page_contract_lite/runtime_scope_closure_batch_32.md --readiness-script scripts/verify/unified_page_contract_lite_phase1_readiness_guard.py --makefile Makefile --report artifacts/backend/unified_page_contract_lite_runtime_scope_closure.json

verify.unified_page_contract.lite.phase1_closure: guard.prod.forbid
	@python3 scripts/verify/unified_page_contract_lite_phase1_closure_guard.py --closure-doc docs/architecture/unified_page_contract_lite/phase1_closure_batch_36.md --iteration-log docs/ops/iterations/delivery_context_switch_log_v1.md --makefile Makefile --report artifacts/backend/unified_page_contract_lite_phase1_closure.json

verify.unified_page_contract.lite.phase2_candidate_plan: guard.prod.forbid
	@python3 scripts/verify/unified_page_contract_lite_phase2_candidate_plan_guard.py --plan docs/architecture/unified_page_contract_lite/phase2_candidate_plan_batch_37.md --phase1-closure docs/architecture/unified_page_contract_lite/phase1_closure_batch_36.md --makefile Makefile --report artifacts/backend/unified_page_contract_lite_phase2_candidate_plan.json

verify.unified_page_contract.lite.phase2_load_contract_gate: guard.prod.forbid
	@python3 scripts/verify/unified_page_contract_lite_phase2_load_contract_gate_guard.py --gate docs/architecture/unified_page_contract_lite/phase2_load_contract_gate_batch_38.md --candidate-plan docs/architecture/unified_page_contract_lite/phase2_candidate_plan_batch_37.md --makefile Makefile --report artifacts/backend/unified_page_contract_lite_phase2_load_contract_gate.json

verify.unified_page_contract.lite.phase3_ui_contract_risk: guard.prod.forbid
	@python3 scripts/verify/unified_page_contract_lite_phase3_ui_contract_risk_guard.py --review docs/architecture/unified_page_contract_lite/phase3_ui_contract_risk_review_batch_42.md --preview-doc docs/architecture/unified_page_contract_lite/phase2_load_contract_preview_batch_39.md --makefile Makefile --report artifacts/backend/unified_page_contract_lite_phase3_ui_contract_risk.json

verify.unified_page_contract.lite.frontend_pilot_readiness: guard.prod.forbid
	@python3 scripts/verify/unified_page_contract_lite_frontend_controlled_pilot_readiness_guard.py --readiness-doc docs/architecture/unified_page_contract_lite/frontend_controlled_pilot_readiness_batch_43.md --risk-review docs/architecture/unified_page_contract_lite/phase3_ui_contract_risk_review_batch_42.md --makefile Makefile --report artifacts/backend/unified_page_contract_lite_frontend_pilot_readiness.json

verify.unified_page_contract.lite.contract_freeze_v2_0: guard.prod.forbid
	@python3 scripts/verify/unified_page_contract_lite_contract_freeze_v2_0_guard.py --freeze-doc docs/architecture/unified_page_contract_lite/frontend_consumption_contract_freeze_v2_0_batch_44.md --schema docs/architecture/unified_page_contract_lite/unified_page_contract_lite.schema.json --example docs/architecture/unified_page_contract_lite/project_form_lite.example.json --patch docs/architecture/unified_page_contract_lite/patch_lite.example.json --makefile Makefile --report artifacts/backend/unified_page_contract_lite_contract_freeze_v2_0.json

verify.unified_page_contract.lite.mainline_absorption: guard.prod.forbid
	@python3 scripts/verify/unified_page_contract_lite_mainline_absorption_guard.py --checkpoint-doc docs/architecture/unified_page_contract_lite/mainline_absorption_checkpoint_batch_47.md --makefile Makefile --report artifacts/backend/unified_page_contract_lite_mainline_absorption.json

verify.unified_page_contract.lite.rollout_switch: guard.prod.forbid
	@python3 scripts/verify/unified_page_contract_lite_rollout_switch_guard.py --report artifacts/backend/unified_page_contract_lite_rollout_switch.json

verify.unified_page_contract.lite.mainline_readiness: verify.unified_page_contract.lite.rollout_switch
	@python3 scripts/verify/unified_page_contract_lite_mainline_readiness_guard.py --report artifacts/backend/unified_page_contract_lite_mainline_readiness.json

verify.unified_page_contract.lite.terminal_client_parity: guard.prod.forbid
	@python3 scripts/verify/unified_page_contract_lite_terminal_client_parity_guard.py --contract docs/architecture/unified_page_contract_lite/project_form_lite.example.json --contract docs/architecture/unified_page_contract_lite/snapshots/project_form_lite_adapter_snapshot_v1.json --contract docs/architecture/unified_page_contract_lite/snapshots/project_tree_lite_adapter_snapshot_v1.json --contract docs/architecture/unified_page_contract_lite/snapshots/project_search_lite_adapter_snapshot_v1.json --patch docs/architecture/unified_page_contract_lite/patch_lite.example.json --patch docs/architecture/unified_page_contract_lite/snapshots/onchange_patch_lite_adapter_snapshot_v1.json --patch docs/architecture/unified_page_contract_lite/snapshots/onchange_patch_complex_lite_adapter_snapshot_v1.json --plan-doc docs/architecture/unified_page_contract_lite/all_terminal_coverage_plan_batch_54.md --makefile Makefile --report artifacts/backend/unified_page_contract_lite_terminal_client_parity.json

verify.unified_page_contract.lite.terminal_coverage_matrix: verify.unified_page_contract.lite.terminal_client_parity
	@python3 scripts/verify/unified_page_contract_lite_terminal_coverage_matrix_guard.py --parity-report artifacts/backend/unified_page_contract_lite_terminal_client_parity.json --plan-doc docs/architecture/unified_page_contract_lite/all_terminal_coverage_plan_batch_54.md --parity-doc docs/architecture/unified_page_contract_lite/terminal_client_parity_batch_55.md --matrix-doc docs/architecture/unified_page_contract_lite/terminal_coverage_matrix_batch_56.md --makefile Makefile --report artifacts/backend/unified_page_contract_lite_terminal_coverage_matrix.json

verify.unified_page_contract.lite.terminal_consumer_boundary: guard.prod.forbid
	@python3 scripts/verify/unified_page_contract_lite_terminal_consumer_boundary_guard.py --report artifacts/backend/unified_page_contract_lite_terminal_consumer_boundary.json

verify.unified_page_contract.lite.wx_mini_renderer_input_pilot.host: verify.unified_page_contract.lite.terminal_consumer_boundary
	@python3 scripts/verify/unified_page_contract_lite_wx_mini_renderer_input_pilot_guard.py --report artifacts/backend/unified_page_contract_lite_wx_mini_renderer_input_pilot.json

verify.unified_page_contract.lite.harmony_h5_renderer_input_pilot.host: verify.unified_page_contract.lite.terminal_consumer_boundary
	@python3 scripts/verify/unified_page_contract_lite_harmony_h5_renderer_input_pilot_guard.py --report artifacts/backend/unified_page_contract_lite_harmony_h5_renderer_input_pilot.json

verify.unified_page_contract.lite.wx_mini_ui_renderer_pilot.host: verify.unified_page_contract.lite.wx_mini_renderer_input_pilot.host
	@python3 scripts/verify/unified_page_contract_lite_wx_mini_ui_renderer_pilot_guard.py --report artifacts/backend/unified_page_contract_lite_wx_mini_ui_renderer_pilot.json

verify.unified_page_contract.lite.harmony_h5_ui_renderer_pilot.host: verify.unified_page_contract.lite.harmony_h5_renderer_input_pilot.host
	@python3 scripts/verify/unified_page_contract_lite_harmony_h5_ui_renderer_pilot_guard.py --report artifacts/backend/unified_page_contract_lite_harmony_h5_ui_renderer_pilot.json

verify.unified_page_contract.lite.wx_mini_page_integration_pilot.host: verify.unified_page_contract.lite.wx_mini_ui_renderer_pilot.host
	@python3 scripts/verify/unified_page_contract_lite_wx_mini_page_integration_pilot_guard.py --report artifacts/backend/unified_page_contract_lite_wx_mini_page_integration_pilot.json

verify.unified_page_contract.lite.harmony_h5_page_integration_pilot.host: verify.unified_page_contract.lite.harmony_h5_ui_renderer_pilot.host
	@python3 scripts/verify/unified_page_contract_lite_harmony_h5_page_integration_pilot_guard.py --report artifacts/backend/unified_page_contract_lite_harmony_h5_page_integration_pilot.json

verify.unified_page_contract.lite.wx_mini_runtime_mount_pilot.host: verify.unified_page_contract.lite.wx_mini_page_integration_pilot.host
	@python3 scripts/verify/unified_page_contract_lite_wx_mini_runtime_mount_pilot_guard.py --report artifacts/backend/unified_page_contract_lite_wx_mini_runtime_mount_pilot.json

verify.unified_page_contract.lite.harmony_h5_runtime_mount_pilot.host: verify.unified_page_contract.lite.harmony_h5_page_integration_pilot.host
	@python3 scripts/verify/unified_page_contract_lite_harmony_h5_runtime_mount_pilot_guard.py --report artifacts/backend/unified_page_contract_lite_harmony_h5_runtime_mount_pilot.json

verify.unified_page_contract.lite.wx_mini_compile_pilot.host: verify.unified_page_contract.lite.wx_mini_runtime_mount_pilot.host
	@python3 scripts/verify/unified_page_contract_lite_wx_mini_compile_pilot_guard.py --report artifacts/backend/unified_page_contract_lite_wx_mini_compile_pilot.json

verify.unified_page_contract.lite.wx_mini_real_compile_pilot.host: verify.unified_page_contract.lite.wx_mini_compile_pilot.host
	@python3 scripts/verify/unified_page_contract_lite_wx_mini_real_compile_pilot_guard.py --report artifacts/backend/unified_page_contract_lite_wx_mini_real_compile_pilot.json --execute

verify.unified_page_contract.lite.wx_mini_runtime_acceptance_pilot.host: verify.unified_page_contract.lite.wx_mini_real_compile_pilot.host
	@python3 scripts/verify/unified_page_contract_lite_wx_mini_runtime_acceptance_pilot_guard.py --report artifacts/backend/unified_page_contract_lite_wx_mini_runtime_acceptance_pilot.json --execute

verify.unified_page_contract.lite.wx_mini_device_acceptance_pilot.host: verify.unified_page_contract.lite.wx_mini_runtime_acceptance_pilot.host
	@python3 scripts/verify/unified_page_contract_lite_wx_mini_device_acceptance_pilot_guard.py --report artifacts/backend/unified_page_contract_lite_wx_mini_device_acceptance_pilot.json

verify.unified_page_contract.lite.harmony_h5_compile_pilot.host: verify.unified_page_contract.lite.harmony_h5_runtime_mount_pilot.host
	@python3 scripts/verify/unified_page_contract_lite_harmony_h5_compile_pilot_guard.py --report artifacts/backend/unified_page_contract_lite_harmony_h5_compile_pilot.json --execute

verify.unified_page_contract.lite.harmony_h5_runtime_acceptance_pilot.host: verify.unified_page_contract.lite.harmony_h5_compile_pilot.host
	@REPORT=artifacts/backend/unified_page_contract_lite_harmony_h5_runtime_acceptance_pilot.json node scripts/verify/unified_page_contract_lite_harmony_h5_runtime_acceptance_pilot.js

verify.unified_page_contract.lite.harmony_h5_device_acceptance_pilot.host: verify.unified_page_contract.lite.harmony_h5_runtime_acceptance_pilot.host
	@python3 scripts/verify/unified_page_contract_lite_harmony_h5_device_acceptance_pilot_guard.py --report artifacts/backend/unified_page_contract_lite_harmony_h5_device_acceptance_pilot.json

.PHONY: verify.native.business_fact.static verify.backend_business_fact.model_audit verify.backend_business_fact.model_standard verify.output_invoice.source_gap_audit
verify.output_invoice.source_gap_audit: guard.prod.forbid
	@python3 -m py_compile scripts/verify/output_invoice_source_gap_audit.py
	@python3 scripts/verify/output_invoice_source_gap_audit.py

verify.backend_business_fact.model_audit: guard.prod.forbid
	@python3 -m py_compile scripts/verify/backend_business_fact_model_audit.py
	@python3 scripts/verify/backend_business_fact_model_audit.py --registry docs/architecture/backend_business_fact_model_standard_registry_v1.json --report artifacts/backend/backend_business_fact_model_audit.json --markdown artifacts/backend/backend_business_fact_model_audit.md

verify.backend_business_fact.model_standard: verify.backend_business_fact.model_audit
	@python3 scripts/verify/backend_business_fact_model_audit.py --enforce --registry docs/architecture/backend_business_fact_model_standard_registry_v1.json --report artifacts/backend/backend_business_fact_model_audit.json --markdown artifacts/backend/backend_business_fact_model_audit.md

verify.native.business_fact.static: guard.prod.forbid
	@bash -n scripts/migration/business_fact_upgrade_replay_flow.sh
	@python3 -m py_compile \
	  scripts/migration/fresh_db_business_fact_replay_postcheck.py \
	  scripts/migration/business_fact_visible_balance_cleanup.py \
	  scripts/migration/business_fact_visible_balance_legacy_source_probe.py \
	  scripts/migration/business_fact_additional_fact_inventory.py \
	  scripts/migration/business_expense_contract_subtype_evidence.py \
	  scripts/migration/business_fact_acceptance_bundle_summary.py \
	  scripts/migration/business_expense_fact_taxonomy_acceptance.py \
	  scripts/migration/business_expense_contract_payment_fact_acceptance.py \
	  scripts/migration/fresh_db_contract_remaining_write.py \
	  scripts/migration/fresh_db_construction_contract_visible_business_fact_write.py \
	  scripts/migration/fresh_db_legacy_supplier_contract_pricing_replay_write.py \
	  scripts/migration/fresh_db_supplier_contract_pricing_projection_write.py \
	  scripts/migration/history_outflow_partner_targeted_replay_write.py \
	  scripts/migration/history_actual_outflow_partner_targeted_replay_write.py \
	  scripts/migration/fresh_db_outflow_request_replay_write.py \
	  scripts/migration/fresh_db_actual_outflow_replay_write.py \
	  scripts/migration/fresh_db_actual_outflow_residual_replay_write.py \
	  scripts/migration/fresh_db_outflow_request_line_replay_write.py \
	  scripts/migration/fresh_db_actual_outflow_line_replay_write.py \
	  scripts/migration/history_payment_request_outflow_state_activation_write.py \
	  scripts/migration/history_payment_request_outflow_approved_recovery_write.py \
	  scripts/migration/history_payment_request_outflow_done_recovery_write.py \
	  scripts/migration/fresh_db_legacy_payment_residual_replay_write.py \
	  scripts/migration/fresh_db_payment_execution_projection_write.py \
	  scripts/migration/fresh_db_actual_outflow_line_payment_execution_projection_write.py \
	  scripts/migration/fresh_db_legacy_deduction_adjustment_line_replay_write.py \
	  scripts/migration/fresh_db_settlement_adjustment_projection_write.py

verify.unified_page_contract.lite: guard.prod.forbid
	@python3 -m py_compile addons/smart_core/core/unified_page_contract_lite_adapter.py addons/smart_core/core/unified_page_contract_lite_source_normalizer.py addons/smart_core/core/unified_page_contract_lite_patch_normalizer.py addons/smart_core/core/unified_page_contract_lite_preview.py addons/smart_core/handlers/api_onchange.py addons/smart_core/handlers/load_contract.py scripts/verify/unified_page_contract_lite_guard.py scripts/verify/unified_page_contract_lite_mapping_guard.py scripts/verify/unified_page_contract_lite_adapter_guard.py scripts/verify/unified_page_contract_lite_runtime_boundary_guard.py scripts/verify/unified_page_contract_lite_source_guard.py scripts/verify/unified_page_contract_lite_source_normalizer_guard.py scripts/verify/unified_page_contract_lite_patch_normalizer_guard.py scripts/verify/unified_page_contract_lite_pipeline_guard.py scripts/verify/unified_page_contract_lite_phase1_readiness_guard.py scripts/verify/unified_page_contract_lite_integration_plan_guard.py scripts/verify/unified_page_contract_lite_opt_in_envelope_guard.py scripts/verify/unified_page_contract_lite_opt_in_response_guard.py scripts/verify/unified_page_contract_lite_opt_in_negative_guard.py scripts/verify/unified_page_contract_lite_acceptance_checklist_guard.py scripts/verify/unified_page_contract_lite_api_onchange_preview_guard.py scripts/verify/unified_page_contract_lite_api_onchange_preview_behavior_guard.py scripts/verify/unified_page_contract_lite_integration_validation_matrix_guard.py scripts/verify/unified_page_contract_lite_api_onchange_preview_interface_probe.py scripts/verify/unified_page_contract_lite_api_onchange_preview_intent_smoke.py scripts/verify/unified_page_contract_lite_startup_chain_negative_smoke.py scripts/verify/unified_page_contract_lite_load_contract_negative_smoke.py scripts/verify/unified_page_contract_lite_load_contract_preview_interface_probe.py scripts/verify/unified_page_contract_lite_load_contract_preview_intent_smoke.py scripts/verify/unified_page_contract_lite_load_contract_preview_matrix_smoke.py scripts/verify/unified_page_contract_lite_frontend_runtime_negative_guard.py scripts/verify/unified_page_contract_lite_runtime_scope_closure_guard.py scripts/verify/unified_page_contract_lite_phase1_closure_guard.py scripts/verify/unified_page_contract_lite_phase2_candidate_plan_guard.py scripts/verify/unified_page_contract_lite_phase2_load_contract_gate_guard.py scripts/verify/unified_page_contract_lite_phase3_ui_contract_risk_guard.py scripts/verify/unified_page_contract_lite_frontend_controlled_pilot_readiness_guard.py scripts/verify/unified_page_contract_lite_contract_freeze_v2_0_guard.py scripts/verify/unified_page_contract_lite_frontend_pilot_implementation_guard.py scripts/verify/unified_page_contract_lite_mainline_absorption_guard.py scripts/verify/unified_page_contract_lite_rollout_switch_guard.py scripts/verify/unified_page_contract_lite_mainline_readiness_guard.py scripts/verify/unified_page_contract_lite_terminal_client_parity_guard.py scripts/verify/unified_page_contract_lite_terminal_coverage_matrix_guard.py scripts/verify/unified_page_contract_lite_terminal_consumer_boundary_guard.py scripts/verify/unified_page_contract_lite_wx_mini_renderer_input_pilot_guard.py scripts/verify/unified_page_contract_lite_harmony_h5_renderer_input_pilot_guard.py scripts/verify/unified_page_contract_lite_wx_mini_ui_renderer_pilot_guard.py scripts/verify/unified_page_contract_lite_harmony_h5_ui_renderer_pilot_guard.py scripts/verify/unified_page_contract_lite_wx_mini_page_integration_pilot_guard.py scripts/verify/unified_page_contract_lite_harmony_h5_page_integration_pilot_guard.py scripts/verify/unified_page_contract_lite_wx_mini_runtime_mount_pilot_guard.py scripts/verify/unified_page_contract_lite_harmony_h5_runtime_mount_pilot_guard.py scripts/verify/unified_page_contract_lite_wx_mini_compile_pilot_guard.py scripts/verify/unified_page_contract_lite_wx_mini_real_compile_pilot_guard.py scripts/verify/unified_page_contract_lite_wx_mini_runtime_acceptance_pilot_guard.py scripts/verify/unified_page_contract_lite_wx_mini_device_acceptance_pilot_guard.py scripts/verify/unified_page_contract_lite_harmony_h5_compile_pilot_guard.py scripts/verify/unified_page_contract_lite_harmony_h5_device_acceptance_pilot_guard.py
	@python3 scripts/verify/unified_page_contract_lite_guard.py --schema docs/architecture/unified_page_contract_lite/unified_page_contract_lite.schema.json --example docs/architecture/unified_page_contract_lite/project_form_lite.example.json --patch docs/architecture/unified_page_contract_lite/patch_lite.example.json
	@python3 scripts/verify/unified_page_contract_lite_source_guard.py --contract-source-schema docs/architecture/unified_page_contract_lite/lite_adapter_source.schema.json --patch-source-schema docs/architecture/unified_page_contract_lite/lite_adapter_patch_source.schema.json --contract-source docs/architecture/unified_page_contract_lite/fixtures/project_form_semantic_source_v1.json --contract-source docs/architecture/unified_page_contract_lite/fixtures/project_tree_semantic_source_v1.json --contract-source docs/architecture/unified_page_contract_lite/fixtures/project_search_semantic_source_v1.json --contract-source docs/architecture/unified_page_contract_lite/snapshots/legacy_project_form_normalized_source_snapshot_v1.json --patch-source docs/architecture/unified_page_contract_lite/fixtures/onchange_patch_source_v1.json --patch-source docs/architecture/unified_page_contract_lite/fixtures/onchange_patch_complex_source_v1.json --patch-source docs/architecture/unified_page_contract_lite/snapshots/legacy_onchange_normalized_patch_source_snapshot_v1.json
	@python3 scripts/verify/unified_page_contract_lite_source_normalizer_guard.py --raw-source docs/architecture/unified_page_contract_lite/fixtures/legacy_project_form_raw_source_v1.json --normalized-snapshot docs/architecture/unified_page_contract_lite/snapshots/legacy_project_form_normalized_source_snapshot_v1.json
	@python3 scripts/verify/unified_page_contract_lite_patch_normalizer_guard.py --raw-patch docs/architecture/unified_page_contract_lite/fixtures/legacy_onchange_raw_patch_source_v1.json --normalized-snapshot docs/architecture/unified_page_contract_lite/snapshots/legacy_onchange_normalized_patch_source_snapshot_v1.json
	@python3 scripts/verify/unified_page_contract_lite_pipeline_guard.py --raw-contract-source docs/architecture/unified_page_contract_lite/fixtures/legacy_project_form_raw_source_v1.json --contract-snapshot docs/architecture/unified_page_contract_lite/snapshots/legacy_project_form_lite_pipeline_snapshot_v1.json --raw-patch-source docs/architecture/unified_page_contract_lite/fixtures/legacy_onchange_raw_patch_source_v1.json --patch-snapshot docs/architecture/unified_page_contract_lite/snapshots/legacy_onchange_lite_patch_pipeline_snapshot_v1.json
	@python3 scripts/verify/unified_page_contract_lite_opt_in_envelope_guard.py --schema docs/architecture/unified_page_contract_lite/lite_runtime_opt_in_envelope.schema.json --example docs/architecture/unified_page_contract_lite/lite_runtime_opt_in_envelope.example.json --plan docs/architecture/unified_page_contract_lite/runtime_integration_plan_batch_14.md
	@python3 scripts/verify/unified_page_contract_lite_opt_in_response_guard.py --schema docs/architecture/unified_page_contract_lite/lite_runtime_opt_in_response.schema.json --example docs/architecture/unified_page_contract_lite/lite_runtime_opt_in_response.example.json --request-schema docs/architecture/unified_page_contract_lite/lite_runtime_opt_in_envelope.schema.json
	@python3 scripts/verify/unified_page_contract_lite_opt_in_negative_guard.py --positive docs/architecture/unified_page_contract_lite/lite_runtime_opt_in_envelope.example.json --negative docs/architecture/unified_page_contract_lite/fixtures/default_load_contract_request_v1.json --negative docs/architecture/unified_page_contract_lite/fixtures/default_ui_contract_request_v1.json --negative docs/architecture/unified_page_contract_lite/fixtures/default_onchange_request_v1.json --negative docs/architecture/unified_page_contract_lite/fixtures/invalid_lite_preview_missing_version_request_v1.json
	@python3 scripts/verify/unified_page_contract_lite_api_onchange_preview_guard.py
	@python3 scripts/verify/unified_page_contract_lite_api_onchange_preview_behavior_guard.py --legacy-response docs/architecture/unified_page_contract_lite/fixtures/api_onchange_legacy_response_v1.json --report artifacts/backend/unified_page_contract_lite_api_onchange_preview_behavior.json
	@python3 scripts/verify/unified_page_contract_lite_mapping_guard.py --mapping docs/architecture/unified_page_contract_lite/semantic_adapter_mapping_inventory_v1.json
	@python3 scripts/verify/unified_page_contract_lite_adapter_guard.py --contract-source docs/architecture/unified_page_contract_lite/fixtures/project_form_semantic_source_v1.json --contract-snapshot docs/architecture/unified_page_contract_lite/snapshots/project_form_lite_adapter_snapshot_v1.json --contract-case docs/architecture/unified_page_contract_lite/fixtures/project_tree_semantic_source_v1.json docs/architecture/unified_page_contract_lite/snapshots/project_tree_lite_adapter_snapshot_v1.json --contract-case docs/architecture/unified_page_contract_lite/fixtures/project_search_semantic_source_v1.json docs/architecture/unified_page_contract_lite/snapshots/project_search_lite_adapter_snapshot_v1.json --patch-source docs/architecture/unified_page_contract_lite/fixtures/onchange_patch_source_v1.json --patch-snapshot docs/architecture/unified_page_contract_lite/snapshots/onchange_patch_lite_adapter_snapshot_v1.json --patch-case docs/architecture/unified_page_contract_lite/fixtures/onchange_patch_complex_source_v1.json docs/architecture/unified_page_contract_lite/snapshots/onchange_patch_complex_lite_adapter_snapshot_v1.json --report artifacts/backend/unified_page_contract_lite_adapter_coverage.json
	@python3 scripts/verify/unified_page_contract_lite_runtime_boundary_guard.py --report artifacts/backend/unified_page_contract_lite_runtime_boundary.json
	@python3 scripts/verify/unified_page_contract_lite_phase1_readiness_guard.py --adapter-coverage artifacts/backend/unified_page_contract_lite_adapter_coverage.json --runtime-boundary artifacts/backend/unified_page_contract_lite_runtime_boundary.json --report artifacts/backend/unified_page_contract_lite_phase1_readiness.json
	@python3 scripts/verify/unified_page_contract_lite_integration_plan_guard.py --plan docs/architecture/unified_page_contract_lite/runtime_integration_plan_batch_14.md --readiness-report artifacts/backend/unified_page_contract_lite_phase1_readiness.json --report artifacts/backend/unified_page_contract_lite_integration_plan.json
	@python3 scripts/verify/unified_page_contract_lite_acceptance_checklist_guard.py --checklist docs/architecture/unified_page_contract_lite/api_onchange_lite_preview_acceptance_batch_18.md --readiness-report artifacts/backend/unified_page_contract_lite_phase1_readiness.json --integration-plan-report artifacts/backend/unified_page_contract_lite_integration_plan.json --report artifacts/backend/unified_page_contract_lite_acceptance_checklist.json
	@python3 scripts/verify/unified_page_contract_lite_integration_validation_matrix_guard.py --matrix docs/architecture/unified_page_contract_lite/integration_validation_matrix_batch_26.md --report artifacts/backend/unified_page_contract_lite_integration_validation_matrix.json
	@python3 scripts/verify/unified_page_contract_lite_runtime_scope_closure_guard.py --matrix docs/architecture/unified_page_contract_lite/integration_validation_matrix_batch_26.md --closure-doc docs/architecture/unified_page_contract_lite/runtime_scope_closure_batch_32.md --readiness-script scripts/verify/unified_page_contract_lite_phase1_readiness_guard.py --makefile Makefile --report artifacts/backend/unified_page_contract_lite_runtime_scope_closure.json
	@python3 scripts/verify/unified_page_contract_lite_phase1_closure_guard.py --closure-doc docs/architecture/unified_page_contract_lite/phase1_closure_batch_36.md --iteration-log docs/ops/iterations/delivery_context_switch_log_v1.md --makefile Makefile --report artifacts/backend/unified_page_contract_lite_phase1_closure.json
	@python3 scripts/verify/unified_page_contract_lite_phase2_candidate_plan_guard.py --plan docs/architecture/unified_page_contract_lite/phase2_candidate_plan_batch_37.md --phase1-closure docs/architecture/unified_page_contract_lite/phase1_closure_batch_36.md --makefile Makefile --report artifacts/backend/unified_page_contract_lite_phase2_candidate_plan.json
	@python3 scripts/verify/unified_page_contract_lite_phase2_load_contract_gate_guard.py --gate docs/architecture/unified_page_contract_lite/phase2_load_contract_gate_batch_38.md --candidate-plan docs/architecture/unified_page_contract_lite/phase2_candidate_plan_batch_37.md --makefile Makefile --report artifacts/backend/unified_page_contract_lite_phase2_load_contract_gate.json
	@python3 scripts/verify/unified_page_contract_lite_phase3_ui_contract_risk_guard.py --review docs/architecture/unified_page_contract_lite/phase3_ui_contract_risk_review_batch_42.md --preview-doc docs/architecture/unified_page_contract_lite/phase2_load_contract_preview_batch_39.md --makefile Makefile --report artifacts/backend/unified_page_contract_lite_phase3_ui_contract_risk.json
	@python3 scripts/verify/unified_page_contract_lite_frontend_controlled_pilot_readiness_guard.py --readiness-doc docs/architecture/unified_page_contract_lite/frontend_controlled_pilot_readiness_batch_43.md --risk-review docs/architecture/unified_page_contract_lite/phase3_ui_contract_risk_review_batch_42.md --makefile Makefile --report artifacts/backend/unified_page_contract_lite_frontend_pilot_readiness.json
	@python3 scripts/verify/unified_page_contract_lite_contract_freeze_v2_0_guard.py --freeze-doc docs/architecture/unified_page_contract_lite/frontend_consumption_contract_freeze_v2_0_batch_44.md --schema docs/architecture/unified_page_contract_lite/unified_page_contract_lite.schema.json --example docs/architecture/unified_page_contract_lite/project_form_lite.example.json --patch docs/architecture/unified_page_contract_lite/patch_lite.example.json --makefile Makefile --report artifacts/backend/unified_page_contract_lite_contract_freeze_v2_0.json
	@python3 scripts/verify/unified_page_contract_lite_frontend_runtime_negative_guard.py --report artifacts/backend/unified_page_contract_lite_frontend_runtime_negative.json
	@python3 scripts/verify/unified_page_contract_lite_frontend_pilot_implementation_guard.py --makefile Makefile --runtime-negative-report artifacts/backend/unified_page_contract_lite_frontend_runtime_negative.json --report artifacts/backend/unified_page_contract_lite_frontend_pilot_implementation.json
	@python3 scripts/verify/unified_page_contract_lite_mainline_absorption_guard.py --checkpoint-doc docs/architecture/unified_page_contract_lite/mainline_absorption_checkpoint_batch_47.md --makefile Makefile --report artifacts/backend/unified_page_contract_lite_mainline_absorption.json
	@python3 scripts/verify/unified_page_contract_lite_rollout_switch_guard.py --report artifacts/backend/unified_page_contract_lite_rollout_switch.json
	@python3 scripts/verify/unified_page_contract_lite_mainline_readiness_guard.py --report artifacts/backend/unified_page_contract_lite_mainline_readiness.json
	@python3 scripts/verify/unified_page_contract_lite_terminal_client_parity_guard.py --contract docs/architecture/unified_page_contract_lite/project_form_lite.example.json --contract docs/architecture/unified_page_contract_lite/snapshots/project_form_lite_adapter_snapshot_v1.json --contract docs/architecture/unified_page_contract_lite/snapshots/project_tree_lite_adapter_snapshot_v1.json --contract docs/architecture/unified_page_contract_lite/snapshots/project_search_lite_adapter_snapshot_v1.json --patch docs/architecture/unified_page_contract_lite/patch_lite.example.json --patch docs/architecture/unified_page_contract_lite/snapshots/onchange_patch_lite_adapter_snapshot_v1.json --patch docs/architecture/unified_page_contract_lite/snapshots/onchange_patch_complex_lite_adapter_snapshot_v1.json --plan-doc docs/architecture/unified_page_contract_lite/all_terminal_coverage_plan_batch_54.md --makefile Makefile --report artifacts/backend/unified_page_contract_lite_terminal_client_parity.json
	@python3 scripts/verify/unified_page_contract_lite_terminal_coverage_matrix_guard.py --parity-report artifacts/backend/unified_page_contract_lite_terminal_client_parity.json --plan-doc docs/architecture/unified_page_contract_lite/all_terminal_coverage_plan_batch_54.md --parity-doc docs/architecture/unified_page_contract_lite/terminal_client_parity_batch_55.md --matrix-doc docs/architecture/unified_page_contract_lite/terminal_coverage_matrix_batch_56.md --makefile Makefile --report artifacts/backend/unified_page_contract_lite_terminal_coverage_matrix.json
	@python3 scripts/verify/unified_page_contract_lite_terminal_consumer_boundary_guard.py --report artifacts/backend/unified_page_contract_lite_terminal_consumer_boundary.json
	@python3 scripts/verify/unified_page_contract_lite_wx_mini_renderer_input_pilot_guard.py --report artifacts/backend/unified_page_contract_lite_wx_mini_renderer_input_pilot.json
	@python3 scripts/verify/unified_page_contract_lite_harmony_h5_renderer_input_pilot_guard.py --report artifacts/backend/unified_page_contract_lite_harmony_h5_renderer_input_pilot.json
	@python3 scripts/verify/unified_page_contract_lite_wx_mini_ui_renderer_pilot_guard.py --report artifacts/backend/unified_page_contract_lite_wx_mini_ui_renderer_pilot.json
	@python3 scripts/verify/unified_page_contract_lite_harmony_h5_ui_renderer_pilot_guard.py --report artifacts/backend/unified_page_contract_lite_harmony_h5_ui_renderer_pilot.json
	@python3 scripts/verify/unified_page_contract_lite_wx_mini_page_integration_pilot_guard.py --report artifacts/backend/unified_page_contract_lite_wx_mini_page_integration_pilot.json
	@python3 scripts/verify/unified_page_contract_lite_harmony_h5_page_integration_pilot_guard.py --report artifacts/backend/unified_page_contract_lite_harmony_h5_page_integration_pilot.json
	@python3 scripts/verify/unified_page_contract_lite_wx_mini_runtime_mount_pilot_guard.py --report artifacts/backend/unified_page_contract_lite_wx_mini_runtime_mount_pilot.json
	@python3 scripts/verify/unified_page_contract_lite_harmony_h5_runtime_mount_pilot_guard.py --report artifacts/backend/unified_page_contract_lite_harmony_h5_runtime_mount_pilot.json
	@python3 scripts/verify/unified_page_contract_lite_wx_mini_compile_pilot_guard.py --report artifacts/backend/unified_page_contract_lite_wx_mini_compile_pilot.json
	@python3 scripts/verify/unified_page_contract_lite_wx_mini_real_compile_pilot_guard.py --report artifacts/backend/unified_page_contract_lite_wx_mini_real_compile_pilot.json --execute
	@python3 scripts/verify/unified_page_contract_lite_wx_mini_runtime_acceptance_pilot_guard.py --report artifacts/backend/unified_page_contract_lite_wx_mini_runtime_acceptance_pilot.json --execute
	@python3 scripts/verify/unified_page_contract_lite_wx_mini_device_acceptance_pilot_guard.py --report artifacts/backend/unified_page_contract_lite_wx_mini_device_acceptance_pilot.json
	@python3 scripts/verify/unified_page_contract_lite_harmony_h5_compile_pilot_guard.py --report artifacts/backend/unified_page_contract_lite_harmony_h5_compile_pilot.json --execute
	@REPORT=artifacts/backend/unified_page_contract_lite_harmony_h5_runtime_acceptance_pilot.json node scripts/verify/unified_page_contract_lite_harmony_h5_runtime_acceptance_pilot.js
	@python3 scripts/verify/unified_page_contract_lite_harmony_h5_device_acceptance_pilot_guard.py --report artifacts/backend/unified_page_contract_lite_harmony_h5_device_acceptance_pilot.json

# ----------------------------------------------------------------------
# v1.1 Engineering Convergence quality entries
# ----------------------------------------------------------------------
.PHONY: ci ci.local.quick test.frontend test.unit test.odoo.integration test.contract test.e2e.preflight test.e2e.fixed_data.odoo test.e2e test.all test.inventory test.inventory.summary test.e2e.matrix architecture.module_dependency_map architecture.complexity_report architecture.complexity_baseline_lock architecture.split_plan_queue github.remote_execution_plan security.secrets.scan

ci: guard.prod.forbid security.secrets.scan test.inventory test.inventory.summary test.e2e.matrix architecture.module_dependency_map architecture.complexity_report architecture.complexity_baseline_lock architecture.split_plan_queue verify.unified_page_contract.v2.web_architecture github.remote_execution_plan test.unit test.frontend test.contract test.e2e.preflight
	@git diff --check
	@echo "[OK] v1.1 PR quality gate passed"

ci.local.quick: guard.prod.forbid architecture.complexity_baseline_lock verify.unified_page_contract.v2.web_architecture
	@python3 scripts/ci/verify_contract_form_split_evidence.py
	@python3 scripts/verify/contract_form_runtime_state_protocol_guard.py
	@scripts/verify/contract_form_runtime_state_behavior_guard.sh
	@python3 scripts/verify/contract_form_side_effect_regression_guard.py
	@python3 scripts/verify/contract_form_behavior_regression_runbook_guard.py
	@python3 scripts/verify/contract_form_onchange_normalization_guard.py
	@python3 scripts/verify/contract_form_action_plan_builder_guard.py
	@python3 scripts/verify/contract_form_save_payload_builder_guard.py
	@python3 scripts/verify/contract_governance_responsibility_map_guard.py
	@python3 scripts/verify/contract_governance_registry_split_guard.py
	@python3 scripts/verify/contract_governance_user_surface_split_guard.py
	@python3 scripts/verify/contract_governance_capabilities_split_guard.py
	@python3 scripts/verify/contract_governance_scenes_split_guard.py
	@python3 scripts/verify/contract_governance_list_surface_split_guard.py
	@python3 scripts/verify/contract_governance_native_bridge_split_guard.py
	@python3 scripts/verify/contract_governance_labels_split_guard.py
	@python3 scripts/verify/contract_governance_access_policy_split_guard.py
	@python3 scripts/verify/contract_governance_canonicalization_split_guard.py
	@python3 scripts/verify/contract_governance_surface_mapping_split_guard.py
	@python3 scripts/verify/contract_governance_create_profile_split_guard.py
	@python3 scripts/verify/contract_governance_field_semantics_split_guard.py
	@python3 scripts/verify/contract_governance_form_layout_split_guard.py
	@python3 scripts/verify/contract_governance_form_actions_split_guard.py
	@python3 scripts/verify/contract_governance_form_render_split_guard.py
	@python3 scripts/verify/contract_governance_form_validation_split_guard.py
	@python3 scripts/verify/frontend_page_contract_boundary_guard.py
	@python3 scripts/verify/frontend_page_contract_orchestration_consumption_guard.py
	@python3 scripts/verify/frontend_contract_consumer_intrusion_guard.py
	@scripts/dev/pnpm_exec.sh -C frontend/apps/web lint:src
	@scripts/dev/pnpm_exec.sh -C frontend/apps/web typecheck:strict
	@git diff --check
	@echo "[OK] local quick gate passed"

test.frontend: guard.prod.forbid
	@scripts/dev/pnpm_exec.sh -C frontend/apps/web lint:src
	@scripts/dev/pnpm_exec.sh -C frontend/apps/web typecheck:strict
	@scripts/dev/pnpm_exec.sh -C frontend/apps/web build

test.unit: guard.prod.forbid
	@python3 scripts/ci/python_syntax_check.py addons/smart_core addons/smart_construction_core scripts/ci scripts/audit scripts/common scripts/e2e

test.odoo.integration: guard.prod.forbid
	@$(MAKE) --no-print-directory ci.smoke

test.contract: guard.prod.forbid
	@node --check frontend/apps/web/scripts/config_workbench_operation_acceptance.mjs
	@node --check frontend/apps/web/scripts/business_form_user_perspective_acceptance.mjs
	@node --check frontend/apps/web/scripts/system_user_experience_shell_acceptance.mjs
	@node --check frontend/apps/web/scripts/user_page_visual_coverage.cjs
	@node --check frontend/apps/web/scripts/system_user_experience_full_browser_summary_guard.mjs

test.e2e.preflight: guard.prod.forbid
	@python3 scripts/e2e/e2e_boq_import_fixed_data_preflight.py >/dev/null
	@python3 scripts/e2e/e2e_boq_to_wbs_task_preflight.py >/dev/null
	@python3 scripts/e2e/e2e_settlement_approval_preflight.py >/dev/null
	@echo "[OK] v1.1 E2E preflight passed"

test.e2e.fixed_data.odoo: guard.prod.forbid
	@$(RUN_ENV) DB_CI=sc_test_e2e_fixed TEST_TAGS=e2e_fixed_journey CI_LOG=test-e2e-fixed.log CI_ARTIFACT_PURGE=0 bash scripts/ci/run_ci.sh

test.e2e: guard.prod.forbid
	@$(MAKE) --no-print-directory verify.system_user_experience.full_browser

test.all: guard.prod.forbid test.unit test.odoo.integration test.contract test.e2e
	@echo "[OK] v1.1 full test stack passed"

test.inventory:
	@python3 scripts/ci/generate_test_inventory.py

test.inventory.summary:
	@python3 scripts/ci/summarize_test_inventory.py

test.e2e.matrix:
	@python3 scripts/ci/generate_e2e_journey_matrix.py

architecture.module_dependency_map:
	@python3 scripts/ci/generate_module_dependency_map.py

architecture.complexity_report:
	@python3 scripts/ci/generate_complexity_budget_report.py

architecture.complexity_baseline_lock:
	@python3 scripts/ci/enforce_complexity_baseline_lock.py

architecture.split_plan_queue:
	@python3 scripts/ci/generate_split_plan_queue.py

github.remote_execution_plan:
	@python3 scripts/ci/generate_github_remote_execution_plan.py

security.secrets.scan:
	@python3 scripts/ci/secret_scan.py
