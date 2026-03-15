# 意图返回接入场景治理层迭代计划（v1）

日期：2026-03-15  
分支：`feat/scene-productization-wave1`

## 目标定位

将 `system.init / app.init` 的意图返回，从“仅返回场景/导航事实”升级为“返回可审计的场景治理事实”，并确保前端可消费、可回退、可验证。

## 架构定位

- Layer Target：`Platform Layer + Scene Layer + Frontend Layer`
- Module：`addons/smart_core/handlers/system_init.py`、`addons/smart_core/core/*scene*builder.py`、`frontend/apps/web/src/stores/session.ts`、`frontend/apps/web/src/app/resolvers/sceneRegistry.ts`
- Reason：在不破坏既有链路的前提下，分阶段完成治理能力显性化与运行链路产品化。

## 执行纪律

1. 每完成一个任务，必须同步更新本文件中的“状态/证据”。
2. 每次更新必须记录：影响文件、验证命令、结果。
3. 未更新文档的任务视为未完成。

## 任务清单（持续更新）

| ID | 任务 | Layer Target | 状态 | 证据 |
|---|---|---|---|---|
| T1 | 修复前端类型检查基线（`.vue` 声明 + 类型断言） | Frontend | ✅ DONE | `frontend/apps/web/src/env.d.ts`、`frontend/apps/web/src/app/navigationRegistry.ts`；`pnpm -C frontend/apps/web exec tsc --noEmit` 通过 |
| T2 | 后端输出 `scene_ready_contract_v1`（双轨） | Platform + Scene | ✅ DONE | `addons/smart_core/core/scene_ready_contract_builder.py`、`addons/smart_core/handlers/system_init.py` |
| T3 | 前端消费 `scene_ready_contract_v1`（registry 优先） | Frontend | ✅ DONE | `frontend/apps/web/src/app/resolvers/sceneRegistry.ts`、`frontend/apps/web/src/stores/session.ts`、`frontend/apps/web/src/views/SceneView.vue` |
| T4 | 后端输出 `scene_governance_v1`（治理汇总） | Platform + Scene | ✅ DONE | `addons/smart_core/core/scene_governance_payload_builder.py`、`addons/smart_core/handlers/system_init.py` |
| T5 | 前端接收并持久化 `scene_governance_v1` | Frontend | ✅ DONE | `frontend/apps/web/src/stores/session.ts` |
| T6 | 场景治理可视化（SceneHealth/调试面板） | Frontend | ✅ DONE | `frontend/apps/web/src/views/SceneHealthView.vue`：新增 governance runtime 区块展示 `scene_governance_v1.gates/reasons` |
| T7 | 新增治理 guard（验证 `scene_governance_v1` 结构与关键 gates） | Governance/Verify | ✅ DONE | `scripts/verify/scene_governance_payload_guard.py` |
| T8 | 将 guard 接入 Makefile 验证入口 | Governance/Verify | ✅ DONE | `Makefile`：`verify.scene.governance_payload.guard`，并纳入 `verify.scene.runtime_boundary.gate` 依赖 |
| T9 | 建立 Scene DSL 编译流水线骨架（Parser/Validator/Binder/Compiler） | Scene + Platform | ✅ DONE | `addons/smart_core/core/scene_dsl_compiler.py` |
| T10 | 将 `scene_ready_contract_v1` 切换为编译流水线产物（保留回退） | Scene + Platform | ✅ DONE | `addons/smart_core/core/scene_ready_contract_builder.py`（主路径改为 `scene_compile(...)`） |
| T11 | 增加“原生契约绑定覆盖率”指标（scene 维度） | Governance/Verify | ✅ DONE | `scene_ready_contract_v1.meta.base_contract_bound_scene_count` + `compile_issue_scene_count` |
| T12 | 建立原生契约后端资产模型与仓储（替代前端单次触发定位） | Platform | ✅ DONE | `addons/smart_core/models/ui_base_contract_asset.py`、`addons/smart_core/core/ui_base_contract_asset_repository.py`、`addons/smart_core/security/ir.model.access.csv` |
| T13 | `system.init` 接入原生契约资产绑定并注入 scene 编译输入 | Platform + Scene | ✅ DONE | `addons/smart_core/handlers/system_init.py`：`bind_scene_assets(...)` + `nav_meta.ui_base_contract_*` |
| T14 | 增加“原生契约资产覆盖率” guard 并接入运行时边界门禁 | Governance/Verify | ✅ DONE | `scripts/verify/scene_base_contract_asset_coverage_guard.py`、`Makefile`：`verify.scene.base_contract_asset_coverage.guard` 纳入 `verify.scene.runtime_boundary.gate` |
| T15 | 明确并落地“原生契约资产层”边界语义（非主事实源） | Architecture + Platform | ✅ DONE | `docs/architecture/ui_base_contract_asset_layer_design_v1.md`、`addons/smart_core/models/ui_base_contract_asset.py`（字段补齐+active 生命周期约束）、`addons/smart_core/core/ui_base_contract_asset_repository.py`（scope hash/source type/code version） |
| T16 | 建立后端资产生产链路（producer + cron 预热入口） | Platform | ✅ DONE | `addons/smart_core/core/ui_base_contract_asset_producer.py`、`addons/smart_core/models/ui_base_contract_asset.py`（`refresh_assets_for_scene_keys/cron_refresh_ui_base_contract_assets`）、`addons/smart_core/data/ui_base_contract_asset_cron.xml` |
| T17 | 建立事件触发生产入口（队列去抖 + cron 批处理消费） | Platform | ✅ DONE | `addons/smart_core/core/ui_base_contract_asset_event_queue.py`、`addons/smart_core/models/ui_base_contract_asset_event_trigger.py`、`addons/smart_core/models/ui_base_contract_asset.py`（`pop_scene_keys` 消费） |
| T18 | 明确“原生契约消费边界 + 行业编排落位”正式规范 | Architecture | ✅ DONE | `docs/architecture/native_contract_driven_scene_orchestrator_boundary_and_industry_composition_v1.md` |
| T19 | 定义 Scene Orchestrator IO 契约与行业编排接口规范 | Architecture | ✅ DONE | `docs/architecture/scene_orchestrator_io_contract_and_industry_interface_spec_v1.md` |
| T20 | 落地 Scene Orchestrator schema/binding/interface guards 并接入 runtime gate | Governance/Verify | ✅ DONE | `scripts/verify/scene_orchestrator_*_guard.py`（4个）+ `Makefile` 接入 `verify.scene.runtime_boundary.gate` |
| T21 | 增加前端“禁止直连 Base Contract”防回归 guard | Governance/Verify | ✅ DONE | `scripts/verify/frontend_no_base_contract_direct_consume_guard.py` + `Makefile` 接入 `verify.scene.runtime_boundary.gate` |
| T22 | 固化 Orchestrator merge priority 门禁（spec + trace） | Governance/Verify | ✅ DONE | `scripts/verify/scene_orchestrator_merge_priority_guard.py` + `Makefile` 接入 `verify.scene.runtime_boundary.gate` |
| T23 | 增加资产队列观测指标并接入 scene_governance_v1 | Platform + Governance/Verify | ✅ DONE | `addons/smart_core/core/ui_base_contract_asset_event_queue.py`、`addons/smart_core/core/scene_governance_payload_builder.py`、`addons/smart_core/handlers/system_init.py`、`scripts/verify/scene_governance_payload_guard.py` |
| T24 | 增加资产队列趋势基线 guard（上限+增长速率） | Governance/Verify | ✅ DONE | `scripts/verify/scene_asset_queue_trend_guard.py`、`scripts/verify/baselines/scene_asset_queue_trend_guard.json`、`Makefile` 接入 `verify.scene.runtime_boundary.gate` |
| T25 | P1 编排内核硬化：接入 profile/policy/provider 执行阶段 | Scene + Platform | ✅ DONE | `addons/smart_core/core/scene_dsl_compiler.py`（`profile_apply/policy_apply/provider_merge/permission_workflow_gate`）、`addons/smart_core/core/scene_ready_contract_builder.py`（透传 `provider_registry`） |
| T26 | P2 冲突裁决引擎代码化（独立 resolver + 冲突样例） | Scene + Platform + Governance/Verify | ✅ DONE | `addons/smart_core/core/scene_merge_resolver.py`、`addons/smart_core/core/scene_dsl_compiler.py`（阶段委托 resolver）、`scripts/verify/scene_orchestrator_merge_priority_guard.py`（冲突样例断言） |
| T27 | 资产覆盖率门禁升级为“结构 + 阈值（环境/角色分层）” | Governance/Verify | ✅ DONE | `scripts/verify/scene_base_contract_asset_coverage_guard.py`、`scripts/verify/baselines/scene_base_contract_asset_coverage_guard.json`、`docs/ops/verify/README.md` |
| T28 | 编排器补齐原生子契约消费（views/fields/actions/validator） | Scene + Platform | ✅ DONE | `addons/smart_core/core/scene_dsl_compiler.py`（base facts 消费扩展、base action 回填、validation surface 注入） |
| T29 | 补齐 blocks 对 form/kanban 的结构化展开（去 list-only） | Scene + Platform | ✅ DONE | `addons/smart_core/core/scene_dsl_compiler.py`（`_infer_block_type`、`_normalize_field_names`、`block_expand(..., ctx)`） |
| T30 | 将 validation_surface 升级为显式输出并前端消费 | Scene + Frontend + Verify | ✅ DONE | `addons/smart_core/core/scene_dsl_compiler.py`、`addons/smart_core/core/scene_ready_contract_builder.py`、`frontend/apps/web/src/app/resolvers/sceneRegistry.ts`、`frontend/apps/web/src/views/SceneView.vue`、`scripts/verify/scene_orchestrator_output_schema_guard.py` |
| T31 | 补齐 base action -> 标准 intent 映射规则并加样例 | Scene + Platform + Verify | ✅ DONE | `addons/smart_core/core/scene_dsl_compiler.py`（`_infer_intent_from_action` + resolution meta）、`scripts/verify/scene_orchestrator_merge_priority_guard.py`（`create_project -> record.create` 样例） |
| T32 | 增加 form/kanban block expansion 运行样例 guard | Scene + Verify | ✅ DONE | `scripts/verify/scene_orchestrator_merge_priority_guard.py`（新增 `projects.record` 运行样例：form/kanban 结构断言） |
| T33 | validation_surface 升级到表单提交前预检 | Frontend + Scene | ✅ DONE | `frontend/apps/web/src/pages/ContractFormPage.vue`（读取 scene-ready `validation_surface.required_fields`，提交前执行 `SCENE_VALIDATION_REQUIRED` 预检） |
| T34 | `SCENE_VALIDATION_REQUIRED` 对齐统一错误码常量 | Frontend | ✅ DONE | `frontend/apps/web/src/app/error_codes.ts`、`frontend/apps/web/src/pages/ContractFormPage.vue`（预检提示改为引用 `ErrorCodes.SCENE_VALIDATION_REQUIRED`） |
| T35 | `SCENE_VALIDATION_REQUIRED` 接入统一错误面板 | Frontend | ✅ DONE | `frontend/apps/web/src/pages/ContractFormPage.vue`（Scene 预检错误改为 `StatusPanel` 展示，含机读 code/reason + suggested action） |
| T36 | `SCENE_VALIDATION_REQUIRED` 推荐动作升级为可执行跳转 | Frontend | ✅ DONE | `frontend/apps/web/src/pages/ContractFormPage.vue`（优先 `open_record:<model>:<id>`，其次 `open_scene:<scene_key>`） |
| T37 | `SCENE_VALIDATION_REQUIRED` 推荐动作场景化策略（模型+角色） | Frontend | ✅ DONE | `frontend/apps/web/src/pages/ContractFormPage.vue`（按 `model/role_code/action_id/scene_key` 策略分流 `open_record/open_action/open_scene`） |
| T38 | `SCENE_VALIDATION_REQUIRED` 场景化策略外置配置化 | Frontend | ✅ DONE | `frontend/apps/web/src/app/sceneValidationRecoveryStrategy.ts`（可配置策略模块） + `frontend/apps/web/src/pages/ContractFormPage.vue`（改为策略调用） |
| T39 | `sceneValidationRecoveryStrategy` 增加运行时覆盖入口 + 守卫 | Frontend + Verify | ✅ DONE | `frontend/apps/web/src/app/sceneValidationRecoveryStrategy.ts`（`applySceneValidationRecoveryStrategyRuntime`）、`frontend/apps/web/src/stores/session.ts`（app.init 运行时接线）、`scripts/verify/scene_validation_recovery_strategy_guard.py`、`Makefile` |
| T40 | `scene_validation_recovery_strategy` 后端下发 schema 固化 | Platform + Frontend + Verify | ✅ DONE | `addons/smart_core/handlers/system_init.py`（显式输出策略 payload + 参数/扩展/ICP 读取）、`scripts/verify/baselines/scene_validation_recovery_strategy_schema_guard.json`、`scripts/verify/scene_validation_recovery_strategy_guard.py`（schema + wiring 校验） |
| T41 | recovery strategy payload 路径稳定性 smoke guard | Platform + Frontend + Verify | ✅ DONE | `scripts/verify/scene_validation_recovery_strategy_payload_path_guard.py`（后端 `params->ext_facts->icp` 与前端 `top-level->ext_facts` 路径优先级校验）、`Makefile`（纳入 `verify.scene.runtime_boundary.gate`） |
| T42 | recovery strategy 端到端链路 smoke guard | Platform + Frontend + Verify | ✅ DONE | `scripts/verify/scene_validation_recovery_strategy_e2e_smoke_guard.py`（后端输出→session 注入→页面 suggestedAction 链路顺序校验）、`Makefile`（纳入 `verify.scene.runtime_boundary.gate`） |
| T43 | recovery strategy 行为样例基线守卫 | Platform + Frontend + Verify | ✅ DONE | `scripts/verify/baselines/scene_validation_recovery_strategy_behavior_smoke_guard.json`、`scripts/verify/scene_validation_recovery_strategy_e2e_smoke_guard.py`（按角色/公司覆盖 `open_record/open_action/open_scene` 行为校验） |
| T44 | 平台原生契约子契约规范化内核（资产化生产链） | Platform + Scene + Verify | ✅ DONE | `addons/smart_core/core/ui_base_contract_canonicalizer.py`（`views/fields/search/permissions/workflow/validator/actions` 规范化）、`addons/smart_core/core/ui_base_contract_asset_producer.py`、`addons/smart_core/core/ui_base_contract_asset_repository.py`、`scripts/verify/scene_ui_base_contract_canonicalizer_guard.py` |
| T45 | 场景编排按 scene_type 深消费子契约 surface | Scene + Platform + Verify | ✅ DONE | `addons/smart_core/core/scene_dsl_compiler.py`（`_infer_scene_type` + `search/workflow/validation` scene_type shaping + `surface_profile`）、`scripts/verify/scene_orchestrator_scene_type_surface_guard.py` |
| T46 | 场景编排 action surface 分层输出（primary/secondary/contextual） | Scene + Platform + Verify | ✅ DONE | `addons/smart_core/core/scene_dsl_compiler.py`（`_infer_action_tier/_build_action_surface` + `action_surface` 输出 + `meta.action_surface_counts`）、`scripts/verify/scene_orchestrator_action_surface_guard.py` |
| T47 | action surface 权限/工作流联动裁决 | Scene + Platform + Verify | ✅ DONE | `addons/smart_core/core/scene_dsl_compiler.py`（`action_permission_workflow_gate`：按 rights + transitions 过滤动作并重建 surface）、`scripts/verify/scene_orchestrator_action_surface_guard.py`（可执行动作样例断言） |
| T48 | action surface role/company 运行时覆写策略 | Scene + Platform + Verify | ✅ DONE | `addons/smart_core/core/scene_dsl_compiler.py`（`_resolve_action_surface_strategy/_apply_action_surface_strategy`，支持 `default/by_role/by_company/by_company_role`）、`scripts/verify/scene_orchestrator_action_surface_guard.py`（覆写分层与 hide 样例断言） |
| T49 | action surface 策略统一下发接入 system.init | Platform + Scene + Verify | ✅ DONE | `addons/smart_core/handlers/system_init.py`（`scene_action_surface_strategy` 统一加载输出）、`addons/smart_core/core/scene_ready_contract_builder.py`（策略+role/company runtime 注入 scene 编译）、`scripts/verify/scene_action_surface_strategy_wiring_guard.py` |
| T50 | action surface 策略 schema 基线与白名单守卫 | Platform + Scene + Verify | ✅ DONE | `scripts/verify/baselines/scene_action_surface_strategy_schema_guard.json`、`scripts/verify/scene_action_surface_strategy_schema_guard.py`、`Makefile`（纳入 `verify.scene.runtime_boundary.gate`） |
| T51 | action surface 策略冲突优先级守卫 | Platform + Scene + Verify | ✅ DONE | `scripts/verify/baselines/scene_action_surface_strategy_priority_guard.json`、`scripts/verify/scene_action_surface_strategy_priority_guard.py`（同 key 冲突优先级样例断言）、`Makefile`（纳入 runtime gate） |
| T52 | scene_ready 子契约消费率指标（分 scene_type） | Scene + Platform + Verify | ✅ DONE | `addons/smart_core/core/scene_ready_contract_builder.py`（`meta.scene_type_consumption_metrics`）、`scripts/verify/scene_ready_scene_type_consumption_metrics_guard.py` |
| T53 | scene_governance 摘要接入 scene_ready 消费率指标 | Scene + Platform + Verify | ✅ DONE | `addons/smart_core/core/scene_governance_payload_builder.py`（`scene_ready_consumption` 摘要 + diagnostics 标记）、`scripts/verify/scene_governance_payload_guard.py` |
| T54 | 前端治理面板接入 scene_ready_consumption 可视化 | Frontend + Verify | ✅ DONE | `frontend/apps/web/src/layouts/AppShell.vue`（HUD 展示 `governance.scene_ready_consumption`）、`frontend/apps/web/src/views/SceneHealthView.vue`（runtime section 展示 consumption 摘要）、`scripts/verify/frontend_scene_governance_consumption_guard.py` |
| T55 | scene_ready_consumption 趋势基线守卫 | Scene + Platform + Verify | ✅ DONE | `scripts/verify/baselines/scene_ready_consumption_trend_guard.json`、`scripts/verify/scene_ready_consumption_trend_guard.py`（聚合消费率下降阈值 + scene/type floor）、`Makefile`（纳入 runtime gate） |
| T56 | 关键场景编译样例回归守卫（原生契约输入闭环） | Scene + Platform + Verify | ✅ DONE | `scripts/verify/baselines/scene_orchestrator_key_scene_compile_guard.json`、`scripts/verify/scene_orchestrator_key_scene_compile_guard.py`（`projects.list/projects.intake/workspace.home` 样例编译断言 scene_type/绑定/surface/pipeline）、`Makefile`（纳入 runtime gate） |
| T57 | action surface strategy 下发 payload baseline 守卫 | Platform + Scene + Verify | ✅ DONE | `addons/smart_core/handlers/system_init.py`（策略输出归一化新增 key 白名单与去重）、`scripts/verify/baselines/scene_action_surface_strategy_payload_guard.json`、`scripts/verify/scene_action_surface_strategy_payload_guard.py`（`system.init` live sample baseline 校验）、`Makefile`（纳入 runtime gate） |
| T58 | scene_governance 历史趋势报告门禁（queue + consumption） | Scene + Platform + Verify | ✅ DONE | `scripts/verify/baselines/scene_governance_history_report_guard.json`、`scripts/verify/scene_governance_history_report_guard.py`（聚合 queue/consumption 趋势状态，输出 JSON+MD 报告并校验策略对齐）、`Makefile`（纳入 runtime gate） |
| T59 | 关键场景真实 registry/资产输入快照回归守卫 | Scene + Platform + Verify | ✅ DONE | `scripts/verify/baselines/scene_registry_asset_snapshot_guard.json`、`scripts/verify/scene_registry_asset_snapshot_guard.py`（`system.init` live/fallback 快照，校验 key scene 覆盖与 base_contract 绑定）、`Makefile`（纳入 runtime gate） |

## 本轮已执行验证

- `python3 -m py_compile addons/smart_core/core/scene_ready_contract_builder.py addons/smart_core/core/scene_governance_payload_builder.py addons/smart_core/handlers/system_init.py`：通过
- `pnpm -C frontend/apps/web exec tsc --noEmit --pretty false`：通过
- `pnpm -C frontend/apps/web exec tsc --noEmit --pretty false`（T6 完成后复验）：通过
- `python3 scripts/verify/scene_governance_payload_guard.py`：通过
- `make verify.scene.governance_payload.guard`：通过
- `pnpm -C frontend/apps/web exec tsc --noEmit --pretty false`（AppShell HUD 治理信息扩展后复验）：通过
- `python3 -m py_compile addons/smart_core/core/scene_dsl_compiler.py addons/smart_core/core/scene_ready_contract_builder.py addons/smart_core/handlers/system_init.py`（T9/T10/T11）：通过
- `python3 -m py_compile addons/smart_core/models/ui_base_contract_asset.py addons/smart_core/core/ui_base_contract_asset_repository.py addons/smart_core/handlers/system_init.py addons/smart_core/core/scene_ready_contract_builder.py addons/smart_core/core/scene_dsl_compiler.py`（T12/T13）：通过
- `python3 scripts/verify/scene_base_contract_asset_coverage_guard.py`（T14）：通过
- `make verify.scene.base_contract_asset_coverage.guard`（T14）：通过
- `python3 -m py_compile addons/smart_core/models/ui_base_contract_asset.py addons/smart_core/core/ui_base_contract_asset_repository.py scripts/verify/scene_base_contract_asset_coverage_guard.py`（T15）：通过
- `python3 -m py_compile addons/smart_core/core/ui_base_contract_asset_producer.py addons/smart_core/models/ui_base_contract_asset.py addons/smart_core/core/ui_base_contract_asset_repository.py scripts/verify/scene_base_contract_asset_coverage_guard.py`（T16）：通过
- `python3 scripts/verify/scene_base_contract_asset_coverage_guard.py`（T16 复验）：通过
- `python3 -m py_compile addons/smart_core/core/ui_base_contract_asset_event_queue.py addons/smart_core/models/ui_base_contract_asset_event_trigger.py addons/smart_core/models/ui_base_contract_asset.py scripts/verify/scene_base_contract_asset_coverage_guard.py`（T17）：通过
- `python3 scripts/verify/scene_base_contract_asset_coverage_guard.py`（T17 复验）：通过
- `python3 scripts/verify/scene_orchestrator_input_schema_guard.py`（T20）：通过
- `python3 scripts/verify/scene_orchestrator_output_schema_guard.py`（T20）：通过
- `python3 scripts/verify/scene_orchestrator_base_fact_binding_guard.py`（T20）：通过
- `python3 scripts/verify/scene_orchestrator_industry_interface_guard.py`（T20）：通过
- `make verify.scene.runtime_boundary.gate`（T20）：通过
- `python3 scripts/verify/frontend_no_base_contract_direct_consume_guard.py`（T21）：通过
- `make verify.scene.runtime_boundary.gate`（T21 复验）：通过
- `python3 scripts/verify/scene_orchestrator_merge_priority_guard.py`（T22）：通过
- `make verify.scene.runtime_boundary.gate`（T22 复验）：通过
- `python3 scripts/verify/scene_governance_payload_guard.py`（T23）：通过
- `make verify.scene.runtime_boundary.gate`（T23 复验）：通过
- `python3 scripts/verify/scene_asset_queue_trend_guard.py`（T24）：通过
- `make verify.scene.runtime_boundary.gate`（T24 复验）：通过
- `python3 -m py_compile addons/smart_core/core/scene_dsl_compiler.py addons/smart_core/core/scene_ready_contract_builder.py`（T25）：通过
- `python3 scripts/verify/scene_orchestrator_input_schema_guard.py`（T25）：通过
- `python3 scripts/verify/scene_orchestrator_output_schema_guard.py`（T25）：通过
- `python3 scripts/verify/scene_orchestrator_base_fact_binding_guard.py`（T25）：通过
- `python3 scripts/verify/scene_orchestrator_merge_priority_guard.py`（T25）：通过
- `make verify.scene.runtime_boundary.gate`（T25 复验）：通过
- `python3 -m py_compile addons/smart_core/core/scene_merge_resolver.py addons/smart_core/core/scene_dsl_compiler.py scripts/verify/scene_orchestrator_merge_priority_guard.py`（T26）：通过
- `python3 scripts/verify/scene_orchestrator_merge_priority_guard.py`（T26）：通过
- `make verify.scene.runtime_boundary.gate`（T26 复验）：通过
- `python3 scripts/verify/scene_base_contract_asset_coverage_guard.py`（T27）：通过
- `make verify.scene.runtime_boundary.gate`（T27 复验）：通过
- `python3 -m py_compile addons/smart_core/core/scene_dsl_compiler.py`（T28）：通过
- `python3 scripts/verify/scene_orchestrator_input_schema_guard.py`（T28）：通过
- `python3 scripts/verify/scene_orchestrator_output_schema_guard.py`（T28）：通过
- `python3 scripts/verify/scene_orchestrator_base_fact_binding_guard.py`（T28）：通过
- `python3 scripts/verify/scene_orchestrator_merge_priority_guard.py`（T28）：通过
- `make verify.scene.runtime_boundary.gate`（T28 复验）：通过
- `python3 -m py_compile addons/smart_core/core/scene_dsl_compiler.py`（T29）：通过
- `python3 scripts/verify/scene_orchestrator_input_schema_guard.py`（T29）：通过
- `python3 scripts/verify/scene_orchestrator_output_schema_guard.py`（T29）：通过
- `python3 scripts/verify/scene_orchestrator_base_fact_binding_guard.py`（T29）：通过
- `python3 scripts/verify/scene_orchestrator_merge_priority_guard.py`（T29）：通过
- `make verify.scene.runtime_boundary.gate`（T29 复验）：通过
- `python3 -m py_compile addons/smart_core/core/scene_dsl_compiler.py addons/smart_core/core/scene_ready_contract_builder.py scripts/verify/scene_orchestrator_output_schema_guard.py`（T30）：通过
- `python3 scripts/verify/scene_orchestrator_input_schema_guard.py`（T30）：通过
- `python3 scripts/verify/scene_orchestrator_output_schema_guard.py`（T30）：通过
- `python3 scripts/verify/scene_orchestrator_base_fact_binding_guard.py`（T30）：通过
- `python3 scripts/verify/scene_orchestrator_merge_priority_guard.py`（T30）：通过
- `pnpm -C frontend/apps/web exec tsc --noEmit`（T30）：通过
- `make verify.scene.runtime_boundary.gate`（T30 复验）：通过
- `python3 -m py_compile addons/smart_core/core/scene_dsl_compiler.py scripts/verify/scene_orchestrator_merge_priority_guard.py`（T31）：通过
- `python3 scripts/verify/scene_orchestrator_input_schema_guard.py`（T31）：通过
- `python3 scripts/verify/scene_orchestrator_output_schema_guard.py`（T31）：通过
- `python3 scripts/verify/scene_orchestrator_base_fact_binding_guard.py`（T31）：通过
- `python3 scripts/verify/scene_orchestrator_merge_priority_guard.py`（T31）：通过
- `make verify.scene.runtime_boundary.gate`（T31 复验）：通过
- `python3 -m py_compile scripts/verify/scene_orchestrator_merge_priority_guard.py`（T32）：通过
- `python3 scripts/verify/scene_orchestrator_merge_priority_guard.py`（T32）：通过
- `make verify.scene.runtime_boundary.gate`（T32 复验）：通过
- `pnpm -C frontend/apps/web exec tsc --noEmit`（T33）：通过
- `make verify.scene.runtime_boundary.gate`（T33 复验）：通过
- `pnpm -C frontend/apps/web exec tsc --noEmit`（T34）：通过
- `make verify.scene.runtime_boundary.gate`（T34 复验）：通过
- `pnpm -C frontend/apps/web exec tsc --noEmit`（T35）：通过
- `make verify.scene.runtime_boundary.gate`（T35 复验）：通过
- `pnpm -C frontend/apps/web exec tsc --noEmit`（T36）：通过
- `make verify.scene.runtime_boundary.gate`（T36 复验）：通过
- `pnpm -C frontend/apps/web exec tsc --noEmit`（T37）：通过
- `make verify.scene.runtime_boundary.gate`（T37 复验）：通过
- `pnpm -C frontend/apps/web exec tsc --noEmit`（T38）：通过
- `make verify.scene.runtime_boundary.gate`（T38 复验）：通过
- `pnpm -C frontend/apps/web exec tsc --noEmit`（T39）：通过
- `python3 scripts/verify/scene_validation_recovery_strategy_guard.py`（T39）：通过
- `make verify.scene.runtime_boundary.gate`（T39 复验）：通过
- `python3 -m py_compile addons/smart_core/handlers/system_init.py scripts/verify/scene_validation_recovery_strategy_guard.py`（T40）：通过
- `python3 scripts/verify/scene_validation_recovery_strategy_guard.py`（T40）：通过
- `pnpm -C frontend/apps/web exec tsc --noEmit`（T40）：通过
- `make verify.scene.runtime_boundary.gate`（T40 复验）：通过
- `python3 scripts/verify/scene_validation_recovery_strategy_payload_path_guard.py`（T41）：通过
- `python3 scripts/verify/scene_validation_recovery_strategy_e2e_smoke_guard.py`（T42）：通过
- `make verify.scene.runtime_boundary.gate`（T42 复验）：通过
- `python3 scripts/verify/scene_validation_recovery_strategy_e2e_smoke_guard.py`（T43 行为样例复验）：通过
- `make verify.scene.runtime_boundary.gate`（T43 复验）：通过
- `python3 scripts/verify/scene_ui_base_contract_canonicalizer_guard.py`（T44）：通过
- `make verify.scene.runtime_boundary.gate`（T44 复验）：通过
- `python3 scripts/verify/scene_orchestrator_scene_type_surface_guard.py`（T45）：通过
- `make verify.scene.runtime_boundary.gate`（T45 复验）：通过
- `python3 scripts/verify/scene_orchestrator_action_surface_guard.py`（T46）：通过
- `make verify.scene.runtime_boundary.gate`（T46 复验）：通过
- `python3 scripts/verify/scene_orchestrator_action_surface_guard.py`（T47 联动复验）：通过
- `make verify.scene.runtime_boundary.gate`（T47 复验）：通过
- `python3 scripts/verify/scene_orchestrator_action_surface_guard.py`（T48 覆写策略复验）：通过
- `make verify.scene.runtime_boundary.gate`（T48 复验）：通过
- `python3 scripts/verify/scene_action_surface_strategy_wiring_guard.py`（T49）：通过
- `make verify.scene.runtime_boundary.gate`（T49 复验）：通过
- `python3 scripts/verify/scene_action_surface_strategy_schema_guard.py`（T50）：通过
- `make verify.scene.runtime_boundary.gate`（T50 复验）：通过
- `python3 scripts/verify/scene_action_surface_strategy_priority_guard.py`（T51）：通过
- `make verify.scene.runtime_boundary.gate`（T51 复验）：通过
- `python3 scripts/verify/scene_ready_scene_type_consumption_metrics_guard.py`（T52）：通过
- `make verify.scene.runtime_boundary.gate`（T52 复验）：通过
- `python3 scripts/verify/scene_governance_payload_guard.py`（T53）：通过
- `make verify.scene.runtime_boundary.gate`（T53 复验）：通过
- `pnpm -C frontend/apps/web exec tsc --noEmit`（T54）：通过
- `python3 scripts/verify/frontend_scene_governance_consumption_guard.py`（T54）：通过
- `make verify.scene.runtime_boundary.gate`（T54 复验）：通过
- `python3 scripts/verify/scene_ready_consumption_trend_guard.py`（T55）：通过
- `make verify.scene.runtime_boundary.gate`（T55 复验）：通过
- `python3 scripts/verify/scene_orchestrator_key_scene_compile_guard.py`（T56）：通过
- `make verify.scene.runtime_boundary.gate`（T56 复验）：通过
- `python3 scripts/verify/scene_action_surface_strategy_payload_guard.py`（T57）：通过
- `make verify.scene.runtime_boundary.gate`（T57 复验）：通过
- `python3 scripts/verify/scene_governance_history_report_guard.py`（T58）：通过
- `make verify.scene.runtime_boundary.gate`（T58 复验）：通过
- `python3 scripts/verify/scene_registry_asset_snapshot_guard.py`（T59）：通过
- `make verify.scene.runtime_boundary.gate`（T59 复验）：通过

## 增量更新记录

- 2026-03-15：`AppShell` HUD 已加入 `scene_governance_v1` 可视化字段（`scene_channel/runtime_source/gates/reasons`），便于调试与运维核查。
- 2026-03-15：已新增治理 payload 示例快照基线：`docs/ops/assessment/scene_governance_payload_snapshot_v1_2026-03-15.json`。
- 2026-03-15：确认架构缺口——`scene_ready` 当前主要来源于 scene catalog，而非 UI Base Contract 编译主链；已立项 T9/T10/T11 修复。
- 2026-03-15：已落地 Scene DSL 编译流水线骨架，并将 `scene_ready_contract_v1` 主路径切到编译器；新增绑定覆盖率指标用于度量“原生契约输入”真实使用率。
- 2026-03-15：已将原生契约升级为后端资产模型 `sc.ui.base.contract.asset`，并在 `system.init` 中按 `scene_key + role + company` 绑定注入到 `ui_base_contract`，不再依赖前端 `ui.contract` 单次触发链路。
- 2026-03-15：已新增 `scene_base_contract_asset_coverage_guard`，并纳入 `verify.scene.runtime_boundary.gate`，形成“资产绑定覆盖率”门禁。
- 2026-03-15：已形成《UI Base Contract Asset Layer 设计说明 v1》，明确资产层定位为治理能力（snapshot/replay/cache/audit），不替代运行时实时生成主链。
- 2026-03-15：已按设计文档补齐资产语义字段（`contract_kind/source_type/scope_hash/generated_at/code_version`），并新增“同作用域仅一个 active”生命周期约束。
- 2026-03-15：已落地资产生产链路：新增 `ui_base_contract_asset_producer`，支持按 scene/action 生成并写入资产；新增 `ir.cron` 预热入口（默认 `active=False`，受控启用）。
- 2026-03-15：已落地事件触发链路：`ir.actions.act_window / ir.ui.view / res.groups` 变更自动入队；cron 按队列批处理消费并触发 `event_queue` 资产刷新。
- 2026-03-15：已落地《原生契约驱动的场景编排层消费边界与行业编排落地设计 v1》，明确编排层“按子契约选吃能力”与行业 `Profile + Policy + Provider` 三件套接入边界。
- 2026-03-15：已落地《Scene Orchestrator 输入/输出契约与行业编排接口规范 v1》，明确 input/output schema、provider 接口、执行顺序与 merge 优先级。
- 2026-03-15：已落地 `verify.scene.orchestrator.*` 四个守卫并纳入 `verify.scene.runtime_boundary.gate`，形成“文档规范 -> 可执行门禁”闭环。
- 2026-03-15：已落地前端防回归守卫 `verify.frontend.no_base_contract_direct_consume.guard`，防止前端绕过 Scene-ready 直接消费 Base Contract。
- 2026-03-15：已落地 `verify.scene.orchestrator.merge_priority.guard`，固化 platform/base/profile/policy/provider/permission 优先级规范与编译轨迹可见性。
- 2026-03-15：已将 merge priority guard 升级为“静态规范 + 最小运行样例”双模校验，确保优先级顺序在运行样例中也可验证。
- 2026-03-15：已将资产队列观测指标注入 `scene_governance_v1.asset_queue`（队列长度、最近更新、消费批次），并纳入治理 payload guard。
- 2026-03-15：已新增资产队列趋势基线门禁 `verify.scene.asset_queue_trend.guard`，按基线限制队列堆积上限与单次增长速度。
- 2026-03-15：已完成 P1 最小内核落地：`profile_apply/policy_apply/provider_merge/permission_workflow_gate` 进入 `scene_compile` 主链，编排阶段不再只是轨迹占位。
- 2026-03-15：已完成 P2 冲突裁决引擎代码化：新增独立 `scene_merge_resolver` 承接 profile/policy/provider/permission 合并逻辑，并在 merge-priority guard 中新增冲突样例（provider 覆盖 policy/base；permission 最终裁决清空 actions）。
- 2026-03-15：已完成资产覆盖率门禁升级：`scene_base_contract_asset_coverage_guard` 新增 env/role 分层阈值策略、live/state 双来源评估与严格模式开关（`SC_BASE_CONTRACT_ASSET_COVERAGE_REQUIRE_LIVE=1`）。
- 2026-03-15：已补齐编排器对原生子契约的实质消费：`generate_surfaces` 扩展消费 `views/fields/search/permissions/workflow/validator/actions`，`action_compile` 支持 base action 候选回填，避免仅靠 DSL 静态 actions。
- 2026-03-15：已补齐 `blocks` 的 `form/kanban` 结构化展开能力：编译器根据 block type/source 自动识别 `form/kanban/list`，并在 form block 输出字段约束摘要，在 kanban block 输出模板可用性标记。
- 2026-03-15：已将 `validation_surface` 从 meta 内嵌升级为 Scene-ready 顶层显式字段，并在前端 scene 路由层接入消费（存在 `required_fields` 时显示约束提示）。
- 2026-03-15：已补齐 base action 到标准 intent 的映射规则（create/update/delete/approve/submit/reject/cancel/export/import/search），并记录 `meta.action_intent_resolution` 统计；merge-priority guard 新增 `create_project -> record.create` 运行样例断言。
- 2026-03-15：已为 `form/kanban` 展开能力新增运行样例 guard，确保编译输出包含 `form` 结构化字段摘要与 `kanban.has_template` 标记，防止回退到 list-only 形态。
- 2026-03-15：已将 `validation_surface` 接入 `ContractFormPage` 提交流程：按 scene-ready `required_fields` 做提交前预检，失败时返回 `SCENE_VALIDATION_REQUIRED` 提示，减少后端拒绝后重试成本。
- 2026-03-15：已将 `SCENE_VALIDATION_REQUIRED` 纳入 `ErrorCodes` 常量并完成预检消费对齐，避免前端硬编码错误码漂移。
- 2026-03-15：已将 `SCENE_VALIDATION_REQUIRED` 预检失败接入统一 `StatusPanel`：展示机读 `error_code/reason_code`，并提供 `suggested-action=copy_reason` 便于快速上报定位。
- 2026-03-15：已将 `SCENE_VALIDATION_REQUIRED` 推荐动作升级为可执行跳转：编辑态优先跳转 `open_record`，创建/场景态跳转 `open_scene`，降低用户修复路径摩擦。
- 2026-03-15：已落地 `SCENE_VALIDATION_REQUIRED` 推荐动作场景化策略：按 `model + role_code + action_id + scene_key` 选择 `open_record/open_action/open_scene`，优先给出最短修复路径。
- 2026-03-15：已将 `SCENE_VALIDATION_REQUIRED` 恢复动作策略外置为 `sceneValidationRecoveryStrategy` 模块，支持后续行业模块按模型/角色覆写策略而无需修改页面代码。
- 2026-03-15：已为 `sceneValidationRecoveryStrategy` 增加运行时覆盖入口：支持 `default/by_role/by_company/by_company_role` 分层覆写，并在 `session.app.init` 按角色与公司注入；新增守卫 `verify.scene.validation_recovery_strategy.guard` 固化接线。
- 2026-03-15：已固化后端下发契约：`system.init` 显式输出 `scene_validation_recovery_strategy`（支持 params/ext_facts/ICP 读取），并以 baseline 守卫约束 schema 顶层与接线完整性。
- 2026-03-15：已新增 payload 路径稳定性守卫 `verify.scene.validation_recovery_strategy.payload_path.guard`，固定后端优先级 `params -> ext_facts -> icp` 与前端优先级 `top-level payload -> ext_facts fallback`，并纳入 `verify.scene.runtime_boundary.gate`。
- 2026-03-15：已新增端到端链路守卫 `verify.scene.validation_recovery_strategy.e2e_smoke.guard`，校验 `system.init -> session runtime apply -> ContractFormPage suggestedAction` 链路接线与顺序稳定性。
- 2026-03-15：已为 `verify.scene.validation_recovery_strategy.e2e_smoke.guard` 增加行为样例基线 `scene_validation_recovery_strategy_behavior_smoke_guard.json`，按角色/公司覆盖 `open_record/open_action/open_scene` 三类输出。
- 2026-03-15：已落地平台原生契约规范化内核 `ui_base_contract_canonicalizer`，并接入资产生产与仓储读写路径，确保 Scene 编排输入稳定具备 `views/fields/search/permissions/workflow/validator/actions` 七类子契约。
- 2026-03-15：已落地 Scene 编排层按 `scene_type` 深消费：`form/workspace` 场景分别对 `search/workflow/validation` surface 做差异化 shaping，并产出 `meta.surface_profile` 用于运行时可观测。
- 2026-03-15：已落地 Scene 编排 `action_surface` 分层输出（`primary/secondary/contextual`），并按 `scene_type + placement + intent` 规则归类，输出 `meta.action_surface_counts` 便于运行时观测。
- 2026-03-15：已落地 `action_permission_workflow_gate`，将 `permission.effective.rights` 与 `workflow.transitions` 纳入动作可执行裁决，避免不可执行动作进入最终 `action_surface`。
- 2026-03-15：已落地 action surface 运行时覆写策略：支持 `default/by_role/by_company/by_company_role` 分层策略，按 key 进行 `force_primary/force_secondary/force_contextual/hide` 动态重排。
- 2026-03-15：已将 action surface runtime 策略上收至 `system.init` 统一下发链路：`params -> ext_facts -> ir.config_parameter`，并在 scene_ready 构建阶段注入 `runtime.role_code/company_id/action_surface_strategy`。
- 2026-03-15：已为 action surface 策略补齐 schema baseline 与白名单守卫，固定顶层结构与策略 key，防止策略形态漂移引发运行时不可预期行为。
- 2026-03-15：已新增 action surface 策略冲突优先级守卫，固定 `default -> by_company -> by_role -> by_company_role` 叠加顺序，确保同 key 冲突时输出可预测。
- 2026-03-15：已为 `scene_ready_contract_v1` 增补按 `scene_type` 聚合的子契约消费率指标（base_fact_consumption_rate + surface_nonempty_rate），用于核心能力提升量化。
- 2026-03-15：已将 `scene_ready_contract_v1` 的消费率指标摘要注入 `scene_governance_v1.scene_ready_consumption`，并在 `diagnostics.scene_ready_consumption_enabled` 暴露开关，便于运行时治理看板直接消费。
- 2026-03-15：已将 `scene_ready_consumption` 接入前端治理可视化：`AppShell HUD` 与 `SceneHealth` 均展示 scene_type 摘要，形成后端指标 -> 治理面板可见闭环。
- 2026-03-15：已新增 `scene_ready_consumption` 趋势基线守卫，按聚合消费率下降阈值与 scene/type 最小覆盖进行持续门禁，防止能力回退。
- 2026-03-15：已新增关键场景编译样例回归守卫，固定 `projects.list/projects.intake/workspace.home` 的“原生契约输入 -> scene-ready 输出”闭环断言（scene_type、base 绑定、search/workflow/validation/action surfaces、compile pipeline）。
- 2026-03-15：已将 `scene_action_surface_strategy` 下发契约升级为“后端归一化 + payload baseline 门禁”：`system.init` 仅输出白名单 top keys 与 strategy keys，并以 live sample 对照基线防止策略形态漂移。
- 2026-03-15：已新增 `scene_governance` 历史趋势报告门禁：将 `scene_asset_queue_trend_state` 与 `scene_ready_consumption_trend_state` 聚合为统一历史报告，纳入 runtime gate 做跨趋势策略对齐校验。
- 2026-03-15：已新增关键场景真实快照回归守卫：从 `system.init -> scene_ready_contract_v1` 抽取 `scene_registry_asset_snapshot`，校验关键 scene 覆盖与 `base_contract_bound_scene_count`，并固化 state 便于后续版本对比。

## 下一步（按顺序）

1. 为 action surface strategy 增加公司/角色冲突 live matrix 样例（覆盖 `default/by_company/by_role/by_company_role` 组合）。
2. 将 `scene_governance_history_report` 接入版本化归档（按分支/提交写入 artifacts 目录并生成 diff 摘要）。
3. 将 `scene_registry_asset_snapshot_state` 与关键场景编译样例守卫联动，产出“样例 vs 真实快照”差异报告。
