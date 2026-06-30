# Low-Code Release Closure Plan 2026-06-30

## Objective

低代码配置进入发布级收口，不再按单个异常点零散修复。后续改动必须围绕菜单配置、表单配置、契约 v2、列表搜索、权限范围、版本管理和升级验证七个验收面推进。

## Acceptance Matrix

| Area | User Outcome | Backend Contract | Frontend Contract | Required Evidence |
| --- | --- | --- | --- | --- |
| 菜单配置 | 可配置范围清晰，配置后办理面严格按配置展示 | `ui.menu.config.policy` 和菜单契约是业务办理菜单唯一配置来源；系统菜单只作为可配置素材，不直接越权进入办理面 | 展示全量可配菜单、已启用状态、可删除能力、范围提示和保存结果 | 菜单配置单测、导航契约测试、浏览器对比配置数据与最终导航 |
| 表单配置 | 字段名称、分组、栏数、显示隐藏、宽度和预览保存可闭环 | 字段策略按模型、动作、视图和角色范围生效；保存后契约可追踪 | 配置面板结构专业，操作记录使用业务名称，预览与运行时一致 | 表单配置单测、低代码表单布局浏览器验收 |
| 契约 v2 | 运行时数据结构稳定，不混入旧来源 | 统一从 v2 契约输出，兼容路径必须声明边界和淘汰状态 | 前端只消费标准契约字段，不依赖后端内部技术名 | v2 边界测试、契约 schema/guard、快照稳定性 |
| 列表搜索 | 所有办理面搜索不清零、不漏搜、不串字段 | 搜索域构造、别名字段、count/export 和列表查询一致 | 搜索输入反馈明确，空结果可解释 | 搜索边界单测、典型办理面浏览器验收 |
| 权限与范围 | 用户只能配置和看到允许范围内能力 | 业务角色、公司、根菜单、系统菜单保护都有硬门禁 | 页面解释“可见业务角色”和可配置范围 | 权限边界测试、越界负例、审计摘要 |
| 配置版本 | 用户知道当前版本、变更内容和如何回滚 | 版本快照可比对、可回滚、可审计 | 版本列表展示差异、发布状态和操作入口 | 版本回滚单测、差异展示验收 |
| 发布升级 | 本地完整验证后再升级开发服务器 | 升级脚本和模块测试可重复 | 浏览器验证固定关键路径 | 本地测试清单、开发服务器升级记录、最终 smoke |

## Iteration Order

1. Inventory: 梳理所有低代码配置入口、运行时消费入口、写入口和兜底入口，形成数据职责表。
2. Functional Closure: 集中修复功能闭环缺口，优先表单配置保存预览、菜单配置全量可配、列表搜索一致性。
3. Boundary Gates: 给菜单范围、业务角色、系统菜单保护、契约 v2 来源和搜索域构造加硬门禁。
4. Observability: 统一返回 `reason_code`、范围字段、配置差异、审计摘要和用户可读名称。
5. Acceptance Automation: 将浏览器验收脚本和后端标签测试纳入固定升级前检查。
6. Release Closure: 本地测试全部通过后整理提交、开 PR 或升级开发服务器。

## Non-Negotiable Rules

- 业务办理导航最终展示必须由用户配置契约决定；系统菜单不能绕过配置直接进入办理面。
- 配置中心必须能看到全量可配置素材，并清楚标识哪些已启用到办理面。
- 表单运行时必须消费已保存配置，保存并预览不能与最终办理页不一致。
- 所有用户可见操作记录必须使用业务名称，不展示内部技术字段名。
- 后端允许兼容旧数据读取，但必须声明来源、记录审计，并不得覆盖 v2 契约主路径。
- 每一轮改动必须有对应验收证据，不能只靠人工主观判断。

## Runtime Responsibility Inventory

### Backend Write Entrypoints

| Capability | Intent | Handler | Responsibility |
| --- | --- | --- | --- |
| 菜单配置加载 | `ui.menu_config.panel.get` | `MenuConfigurationLoadHandler` | 返回可配置菜单素材、已配置策略、范围根状态和业务角色选项 |
| 菜单配置保存 | `ui.menu_config.panel.set` | `MenuConfigurationSaveHandler` | 写入 `ui.menu.config.policy`，同步菜单编排契约 |
| 菜单新增 | `ui.menu_config.menu.create` | `MenuConfigurationCreateHandler` | 创建运行时菜单入口，并写入启用策略 |
| 菜单删除 | `ui.menu_config.menu.delete` | `MenuConfigurationDeleteHandler` | 删除运行时新增菜单，系统菜单只能隐藏不能物理删除 |
| 菜单审计 | `ui.menu_config.audit` | `MenuConfigurationAuditHandler` | 对比配置策略、运行时契约和范围有效性 |
| 菜单回滚/版本 | `ui.menu_config.rollback`, `ui.menu_config.versions` | `MenuConfigurationRollbackHandler`, `MenuConfigurationVersionsHandler` | 读取契约历史并恢复策略 |
| 表单字段策略 | `ui.form_field_policy.set` | `FormFieldPolicySetHandler` | 保存字段显示、标题、分组、只读等策略 |
| 表单排序 | `ui.form_field_order.set` | `FormFieldOrderSetHandler` | 保存字段顺序并同步表单编排契约 |
| 表单批量配置 | `ui.form_field_config.batch_set` | `FormFieldConfigBatchSetHandler` | 统一保存分组、显示隐藏、布局和字段配置 |
| 通用契约保存 | `ui.business_config.contract.save` | `BusinessConfigContractSaveHandler` | 保存 v2 视图编排契约，覆盖表单、列表、搜索、分析等视图能力 |
| 列表搜索配置 | `ui.business_config.list_search.set` | `BusinessConfigListSearchSetHandler` | 保存列表列、搜索过滤器和分组配置 |

### Backend Runtime Consumers

| Runtime | File | Required Rule |
| --- | --- | --- |
| v2 页面契约 | `addons/smart_core/handlers/ui_contract_v2.py` | 只消费标准 v2 契约和声明过的业务配置编排 |
| 页面装配 | `addons/smart_core/app_config_engine/services/assemblers/page_assembler.py` | 只暴露用户可用配置动作，不把配置模型当业务事实 |
| 导航派发 | `addons/smart_core/app_config_engine/services/dispatchers/nav_dispatcher.py` | 业务办理导航按用户菜单配置契约输出 |
| 菜单交付 | `addons/smart_core/delivery/menu_service.py` | 系统菜单只作为素材和兜底来源，不能绕过配置策略 |
| 列表数据 | `addons/smart_core/handlers/api_data.py` | list/count/export/read 的搜索域和别名字段必须一致 |
| 低代码汇总 | `addons/smart_core/handlers/business_config_surface.py` | 对配置中心提供聚合、覆盖率、快照和差异能力 |

### Frontend And Browser Acceptance

| Evidence | Script |
| --- | --- |
| 低代码总体验收 | `frontend/apps/web/scripts/low_code_business_config_acceptance.mjs` |
| 表单运行时一致性 | `frontend/apps/web/scripts/low_code_form_runtime_consistency_acceptance.mjs` |
| 表单分组矩阵 | `frontend/apps/web/scripts/low_code_form_group_matrix_acceptance.mjs` |
| 表单布局运行时 | `frontend/apps/web/scripts/low_code_form_layout_runtime_acceptance.mjs` |
| 菜单与导航对齐 | `frontend/apps/web/scripts/low_code_menu_navigation_alignment_acceptance.mjs` |
| 全局稳定性 | `frontend/apps/web/scripts/low_code_global_stability_acceptance.mjs` |
| 配置路由浏览器验收 | `scripts/verify/business_config_runtime_routes_browser_acceptance.mjs` |

### Existing Guard Targets

`scripts/verify/business_config_guard_inventory.py` 已约束以下发布前目标必须存在并挂接：

- `verify.business_config.guard_inventory`
- `verify.business_config.unit`
- `verify.business_config.coverage`
- `verify.business_config.snapshot`
- `verify.business_config.approval_runtime`
- `verify.business_config.browser_acceptance`
- `verify.business_config.low_code_acceptance`
- `verify.business_config.low_code_runtime_consistency`
- `verify.business_config.low_code_group_matrix`
- `verify.business_config.low_code_layout_runtime`
- `verify.business_config.low_code_menu_navigation_alignment`
- `verify.business_config.low_code_global_stability`

## Current Closure Findings

- 能力矩阵必须使用真实运行 intent，不能使用旧命名或通配符描述能力。`business_config_guard_inventory.py` 已对菜单、表单、列表搜索、审批、版本和覆盖率能力的 authoring intents 做精确校验。
- 旧菜单 intent `ui.menu_configuration.*` 和旧审批 intent `sc.approval_policy_configuration.*` 已列为禁用标记；后续如果重新进入能力矩阵，guard 会失败。
- 当前矩阵里的所有能力虽然标为 `ready`，但 ready 只代表“发布验收体系完整”，不代表用户体验已最终达标。后续功能闭环仍按 Acceptance Matrix 逐项验收。
