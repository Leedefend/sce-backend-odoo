# smart_core 核心模块架构审计 v1

日期：2026-05-06

## 目标

把 `smart_core` 核心模块整理为可治理的体系边界。本文不讨论具体业务模型，而是回答：

- `smart_core` 到底负责什么。
- 哪些内容是 Odoo 原生事实源，哪些只是投影或缓存。
- 当前代码实际在做什么。
- 哪些链路已经越界，必须收口。
- 后续整改的 P0/P1 验收口径。

## 总结判断

`smart_core` 现在不是单一“核心工具模块”。它实际承载了六类能力：

1. Intent 总线和统一 HTTP 入口。
2. Odoo 原生 UI/权限/动作/搜索元数据投影。
3. SPA 页面契约组装和 v2 契约适配。
4. Odoo ORM、按钮、onchange、附件、消息的安全代理。
5. 场景交付、场景包、UI base contract 缓存和发布治理。
6. 若干业务场景切片的编排器。

这些能力可以共存，但边界必须明确。当前最严重的问题是：投影、缓存、配置、治理、运行时装配混在一起，导致缓存表或治理函数可能覆盖 Odoo 原生事实。

## 模块入口

### 主入口

- `/api/v1/intent`
  - 文件：`addons/smart_core/controllers/intent_dispatcher.py`
  - 职责：统一 intent 入口、CORS、匿名白名单、权限检查、结果归一化。
  - 下游：`core.intent_router` -> `core.handler_registry` -> `handlers/*`。

### 旧契约入口

- `/api/contract/get`
  - 文件：`addons/smart_core/app_config_engine/controllers/contract_api.py`
  - 职责：调用 `ContractService` 生成旧 Contract 2.0 结构。
  - 当前定位：兼容链路，不应继续扩张为新主链路。

### 旧菜单入口

- `/api/menu/tree`
- `/api/user_menus`
- `/api/menu/navigation`
  - 文件：`addons/smart_core/controllers/platform_menu_api.py`
  - 当前定位：兼容或专项入口。主导航事实应来自 `system.init`、场景交付和 Odoo menu/action 投影。

## 职责域划分

### A. Intent Runtime Layer

核心文件：

- `controllers/intent_dispatcher.py`
- `core/handler_registry.py`
- `core/intent_router.py`
- `core/base_handler.py`
- `core/intent_execution_result.py`

事实源：

- HTTP request、Odoo session、当前用户 env、handler 注册表。

正确职责：

- 解析请求。
- 选择 handler。
- 注入 `env/su_env/request/context/payload`。
- 对写 intent 做统一权限门禁。
- 归一化响应 envelope。

不得承担：

- 不得解释业务语义。
- 不得生成业务数据。
- 不得绕过 Odoo ACL/record rule。

当前风险：

- handler 自动扫描范围大，intent 类型增长快。
- 写 intent 识别依赖名称正则和 REQUIRED_GROUPS，必须持续用 guard 测试约束。

### B. Native Projection Layer

核心文件：

- `app_config_engine/models/app_model_config.py`
- `app_config_engine/models/app_view_config.py`
- `app_config_engine/models/app_search_config.py`
- `app_config_engine/models/app_permission_config.py`
- `app_config_engine/models/app_action_config.py`
- `app_config_engine/models/app_report_config.py`
- `app_config_engine/models/app_workflow_config.py`
- `app_config_engine/models/app_validator_config.py`
- `app_config_engine/models/app_nav_config.py`

事实源：

- `ir.model`
- `ir.model.fields`
- `ir.ui.view`
- `ir.actions.*`
- `ir.ui.menu`
- `ir.model.access`
- `ir.rule`
- `res.groups`
- `ir.filters`
- `ir.actions.report`
- Odoo model `_sql_constraints`
- Odoo model methods and `mail.activity`

正确职责：

- 把 Odoo 原生事实投影成前端契约。
- 允许缓存，但缓存必须可重建、可丢弃。
- 每个输出必须能说明 `source_authority`。

不得承担：

- 不得成为业务事实主数据。
- 不得人工维护与原生事实重复的字段、权限、动作、搜索事实。
- 不得用缓存覆盖 action-specific 原生视图。

当前确认的问题：

- `app.view.config` 唯一键是 `model + view_type`，不能区分多个 action/view。
- 模拟生产库事实：
  - `project.project` 有 8 个原生 tree view、9 个 tree action，但只有 1 条 `app.view.config(tree)`。
  - `res.partner` 有 7 个原生 tree view、7 个 tree action，但只有 1 条 `app.view.config(tree)`。
  - `payment.request` 有 2 个原生 tree view、6 个 tree action，但只有 1 条 `app.view.config(tree)`。
- 这会让投影缓存误代表动作视图事实，是字段丢失、列漂移、表单能力漂移的结构性原因。

### C. Contract Assembly Layer

核心文件：

- `app_config_engine/services/assemblers/page_assembler.py`
- `app_config_engine/services/contract_service.py`
- `handlers/ui_contract.py`
- `handlers/ui_contract_v2.py`
- `handlers/load_contract.py`
- `handlers/load_view.py`
- `core/unified_page_contract_v2_*.py`
- `core/native_view_contract_projection.py`

事实源：

- Native Projection Layer。
- Odoo action/view/model/search/permission 原生事实。
- 当前用户上下文、语言、多公司上下文。

正确职责：

- 把多块投影合成一个页面契约。
- 按当前用户做权限裁剪。
- 适配前端需要的 v1/v2/lite 契约形状。

不得承担：

- 不得把固定业务列、固定业务治理写死为全局事实。
- 不得在契约装配过程中默认写入全局投影缓存。
- 不得让旧契约链路和新 v2 链路互相覆盖。

当前确认的问题：

- `PageAssembler` 在运行时请求里调用 `_generate_from_*`，读契约时会写/更新投影表。
- `ContractService.finalize_contract` 和 `apply_contract_governance` 与投影组装交织，治理逻辑可覆盖原生视图事实。
- `ui.contract.v2` 通过 compat 包装复用 `ui.contract`，目前仍有旧链路耦合。

### D. Odoo Runtime Proxy Layer

核心 handler：

- `api.data`
- `api.data.create`
- `api.data.unlink`
- `api.data.batch`
- `api.onchange`
- `execute_button`
- `search.favorite.set`
- `file.upload`
- `file.download`
- `chatter.post`
- `chatter.timeline`
- `chatter.activity.schedule`
- `meta.describe_model`
- `permission.check`

事实源：

- Odoo ORM。
- ACL。
- record rule。
- `ir.model.fields`。
- `ir.filters`。
- `ir.attachment`。
- `mail.message`。
- `mail.activity`。
- Odoo model button methods and onchange methods。

正确职责：

- 做安全代理。
- 保持 Odoo 原生语义。
- 对前端提供统一 intent envelope。

不得承担：

- 不得创建第二套业务数据层。
- 不得在代理层重新解释状态机、权限、字段含义。
- 不得前端或 handler 自行合成业务事实。

当前风险：

- 部分 handler 语义上是写代理，但权限边界需要依赖 REQUIRED_GROUPS 和 intent permission guard 持续约束。
- `search.favorite.set` 写入 `ir.filters` 是正确方向，但刷新 `app.search.config` 仍需明确是投影重建，不是第二份搜索事实。

### E. Scene Delivery and Governance Layer

核心目录：

- `delivery/*`
- `governance/*`
- `handlers/app_shell.py`
- `handlers/scene_governance.py`
- `handlers/scene_health.py`
- `handlers/scene_package.py`
- `handlers/scene_packages_installed.py`
- `core/scene_*`
- `core/system_init_*`
- `core/ui_base_contract_asset_*`
- `models/ui_base_contract_asset.py`

事实源：

- `sc.scene`
- `sc.capability`
- Odoo menu/action/group。
- `sc.ui.base.contract.asset` 作为缓存。
- system.init 输出和场景包元数据。

正确职责：

- 交付编排。
- 场景发布、渠道、回滚、包导入导出。
- 把 menu/action/contract 引用组织成前端可消费的场景目录。

不得承担：

- 不得作为业务事实权威。
- 不得复制业务字段、业务权限、业务单据事实。
- 不得越过 Odoo action/view/search/source authority 自行定义页面语义。

当前风险：

- 场景 ready contract、runtime page contract、ui base asset、system.init surface 多条链路并存，容易发生同一页面多源事实竞争。
- 场景层必须只引用事实源，不应承载字段事实。

### F. UI Preference Layer

核心文件：

- `models/user_view_preference.py`
- `handlers/user_view_preference.py`

事实源：

- `res.users`
- `ir.actions.actions`
- 用户 UI 行为。

正确职责：

- 保存用户前端显示偏好，如列显隐、列顺序、列宽。
- scope 必须绑定用户、action/model、view_type。

不得承担：

- 不得影响业务事实。
- 不得作为权限或字段存在性的依据。
- 不得进入场景包或业务模型事实。

当前状态：

- `SOURCE_KIND = ui_only_user_preference` 方向正确。
- 后续需加 guard：偏好只能影响前端显示，不影响契约事实和 ORM read 权限。

### G. Business Slice Orchestration Layer

核心目录：

- `orchestration/*`
- `core/page_orchestration_data_provider.py`
- `core/workspace_home_*`
- `core/industry_orchestration_service_adapter.py`

事实源：

- 工程、合同、付款、结算、成本、风险等业务模型。
- Odoo ORM/read_group。

正确职责：

- 面向特定场景组织事实投影。
- 输出 entry、block、dashboard、workspace home 等前端片段。

不得承担：

- 不得定义客户/供应商、合同、资金等业务事实语义。
- 不得在 `smart_core` 内形成行业主数据规则。
- 行业事实整理应留在业务模块或迁移脚本，不进入核心框架。

当前风险：

- `smart_core` 已经包含一些施工业务切片命名和编排器，核心模块边界被业务场景侵入。
- 这部分后续应迁出到行业模块，或至少标记为 construction adapter，不应属于 framework core。

## 当前目录边界建议

### 应保留在 smart_core framework core

- Intent 总线。
- handler 基类和注册。
- response/trace/error envelope。
- Odoo runtime proxy 的通用能力。
- Native projection 的通用 parser/adapter。
- UI contract v2 adapter。
- UI-only preference 通用模型。

### 应作为 projection/cache 子域，不再叫配置事实

- `app.model.config`
- `app.view.config`
- `app.search.config`
- `app.permission.config`
- `app.action.config`
- `app.report.config`
- `app.workflow.config`
- `app.validator.config`
- `app.menu.config`
- `sc.ui.base.contract.asset`

建议命名方向：

- `app.*.projection`
- `app.*.contract.cache`
- 或保留表名但文档、source meta 和 guard 全部标注 `projection_only/rebuildable/no_business_fact_authority`。

### 应迁出或隔离为 delivery 子域

- 场景包、渠道、发布、回滚、scene health。
- `system.init` 的 scene delivery surface。
- app shell catalog/nav/open。

### 应迁出或隔离为 construction adapter

- 付款、结算、成本、项目执行、项目计划等业务切片编排。
- workspace home 中行业指标部分。

## P0 整改

### P0-1：修复 app.view.config 身份模型

现状：

- 唯一键：`model + view_type`。

目标：

- 至少支持：`model + view_type + view_id`。
- 对 action 契约支持：`model + view_type + action_id + view_id`。

验收：

- 同一模型多个 tree view 不互相覆盖。
- `project.project`、`res.partner`、`payment.request` action-specific tree 能独立投影。
- 页面契约不得从 generic tree 缓存误读 action tree。

### P0-2：运行时只读，生成期写入

现状：

- 页面请求中调用 `_generate_from_*` 并写缓存。

目标：

- 运行时默认只读投影。
- 缺失投影时可即时从 Odoo 原生事实生成内存契约，但不得污染全局缓存。
- 缓存重建由升级、cron、显式管理命令或 precompile 触发。

验收：

- 普通用户打开页面不会写 `app.*.config`。
- 投影重建有明确入口和日志。

### P0-3：治理层不得覆盖事实源

现状：

- `contract_governance` 可用固定列清单重写列表字段。

目标：

- 治理只能做裁剪、排序、展示增强。
- 字段存在性、视图字段、按钮、权限以 Odoo 原生事实和投影为准。

验收：

- 新增原生 tree 字段不会被治理吞掉。
- governance 测试覆盖 `create_uid/create_date` 这类普通字段。

### P0-4：source authority 强制化

目标：

- 所有 handler、projection、contract block 必须声明：
  - `source_kind`
  - `source_authorities`
  - 是否 `projection_only`
  - 是否 `rebuildable`
  - 是否 `no_business_fact_authority`

验收：

- 新增 handler 没有 source authority 时测试失败。
- 场景层、projection 层、runtime proxy 层 source kind 不混用。

### P0-5：核心模块去业务化

目标：

- `smart_core` 不定义行业业务事实。
- 施工行业编排器迁移到 construction 模块或标记 adapter。

验收：

- `smart_core` framework core 中不出现客户/供应商/合同资金事实归类规则。
- 业务切片 source authority 指向业务模型，不在 core 内定义事实。

## P1 整理

- 合并或废弃 `/api/contract/get` 旧链路。
- 明确 `load_contract/load_view/ui.contract/ui.contract.v2` 的主次关系。
- 继续清理未加载空壳文件和重复 metadata 生成样板。
- 给 `app_config_engine/docs/app_config_engine.md` 更新真实架构，不再描述不存在的 `contract/` 子目录。
- 对 `system.init`、scene ready contract、ui base contract asset 做单一事实路径说明。
- 对 `api.data` 系列补齐 Odoo 原生语义对齐测试：domain、context、record rule、active_test、多公司、read_group。

## 立即验收清单

每个 `smart_core` 能力必须回答：

1. 事实源在哪里？
2. 本层是否只是投影、代理或缓存？
3. 如果删除本层缓存，是否能从事实源重建？
4. 是否会改变业务事实？
5. 是否会覆盖 Odoo 原生 action/view/search/permission？
6. 是否按当前用户 env 执行运行时权限？
7. 是否有 source authority 元数据和测试？

答案不是“是投影/代理/缓存”的能力，不应留在 `smart_core` framework core。

## 本专题后续产物

- `smart_core` 模块边界图。
- `app_config_engine` 重命名/降级方案。
- `app.view.config` action-specific 投影设计。
- 运行时写缓存清理方案。
- source authority guard。
- 业务切片迁移清单。

## 执行记录

### 2026-05-06 P0-1/P0-2 第一轮落地

已执行：

- `app.view.config` 增加投影身份字段：
  - `action_id`
  - `source_view_id`
  - `projection_scope`
- 视图投影唯一约束从旧的 `model + view_type` 改为 `projection_scope`。
- action-bound 投影 scope 格式：
  - `action:{action_id}:{model}:{view_type}:view:{view_id}`
- generic 投影 scope 格式：
  - `generic:{model}:{view_type}`
- `PageAssembler` 运行时读取视图契约时启用 `contract_projection_readonly`，即时解析但不写 `app.view.config`。
- 列表首屏数据读取不再回退读取 generic `app.view.config.arch_parsed.columns`。
- 增加边界测试：
  - action scope 必须不同于 generic scope。
  - readonly projection 不得写缓存表。
- prod-sim 已升级并重启。
- prod-sim 旧数据已回填 `projection_scope`。

prod-sim 验证结果：

- `app_view_config` 已存在列：`action_id`、`source_view_id`、`projection_scope`。
- 唯一约束：`app_view_config_uniq_projection_scope`。
- `projection_scope` 空值数：0。
- generic scope 示例：`generic:res.partner:tree`。
- action scope 示例：`action:741:res.partner:tree:view:0`。
- readonly projection 写缓存前后计数：0 -> 0。

### 2026-05-06 P0-3/P0-4 第二轮落地

已执行：

- `contract_governance` 标准列表治理从“固定列覆盖”调整为“治理列优先排序 + 保留原生 view columns”。
- 原生 tree `columns` / `columns_schema` 中存在且模型字段有效的列，不再被标准列表治理吞掉。
- 新增治理边界测试：`payment.request` 原生扩展列、`create_uid`、`create_date` 必须在治理后保留。
- 新增 handler source authority 守卫：注册到 `HANDLER_REGISTRY` 的 handler 必须声明 `SOURCE_KIND` 或 `SOURCE_AUTHORITY`，并且必须声明 `SOURCE_AUTHORITY` 或非空 `SOURCE_AUTHORITIES`。
- 补齐 `chatter.timeline` 的 `SOURCE_KIND = odoo_collaboration_timeline_projection`。

prod-sim 验证结果：

- 注册 handler 缺失 source authority 数：0。
- 付款申请、材料计划、客户、收款列表的 `ui.contract(action_open)` 均保留 `create_uid/create_date`。
- 标准列表治理后，付款申请保留原生扩展列：`operation_strategy`、`is_overpay_risk`。
- 材料计划保留原生扩展列：`material_uom_summary`、`total_plan_qty`、`total_bill_qty`、`total_unplanned_qty`、`line_note_summary`、`line_attachment_count`。

### 2026-05-06 P0-5 第三轮落地

已执行：

- 明确 `BaseSceneEntryOrchestrator` 是 `scene_entry_runtime_projection_adapter`。
- 场景入口编排器统一声明：
  - `projection_only = True`
  - `no_business_fact_authority = True`
  - `adapter_layer = industry_orchestration_adapter`
- 业务切片服务返回的事实来源不再作为 `smart_core` 编排器自身来源对外暴露，而是放入 `delegated_source_authority`。
- 明确 `industry_orchestration_service_adapter` 是 `industry_orchestration_adapter`，只负责连接 extension hook / ORM service。
- 成本切片缺少扩展服务时的降级服务补充 source authority，标记为 degraded projection。
- 新增边界测试：
  - 所有 scene entry orchestrator 必须是 runtime adapter，不得声明业务事实权威。
  - 行业编排服务适配器必须声明 `no_business_fact_authority`。
  - delegated business fact source 只能嵌套在 delegated source 中，不能混入 core adapter authorities。

边界结论：

- `smart_core/orchestration/*` 目前保留为运行时入口契约适配层。
- 业务事实仍由 `smart_construction_core/services/*` 声明和承担。
- 后续如果继续收敛，应将施工行业专属 orchestrator 文件整体迁入 `smart_construction_core`，`smart_core` 仅保留通用 registry/adapter protocol。

### 2026-05-06 P0-6 第四轮落地

已执行：

- `workspace_home_contract_builder` 声明为 `workspace_home_startup_surface_projection`。
- `workspace_home_data_provider` 声明为 `workspace_home_industry_content_provider_adapter`。
- 首页启动面 source authority 明确：
  - 来自 `sc.capability`、`sc.scene`、`scene_ready_contract_v1`、extension facts 与 provider adapter。
  - 本层 `projection_only = True`。
  - 本层 `no_business_fact_authority = True`。
- `workspace_home` 契约输出增加 `source_authority`，让前端/诊断能看到首页只是启动面投影。
- `system_init` 的 delivery identity 从主流程硬编码 `construction` 改为 `_resolve_startup_delivery_identity()`：
  - 优先使用请求参数 `delivery_product_key` / `delivery_base_product_key` / `delivery_edition_key`。
  - 其次允许扩展 hook `smart_core_resolve_startup_delivery_identity` 提供产品身份。
  - 最后才使用 legacy default。
- `ProductPolicyService` 声明为 `delivery_product_policy_projection`：
  - 数据库 `sc.product.policy` / `sc.scene.snapshot` 是优先事实源。
  - `DEFAULT_PRODUCT_POLICY` 是 fallback policy，不是业务事实权威。

边界结论：

- `system.init` 仍是启动面聚合器，只能聚合用户、菜单、能力、场景、投影契约。
- 首页中的 risk/payment/cost 等可展示语义目前仍保留兼容，但已标记为 provider/extension contribution 结果，后续应迁出到行业模块 profile。
- `smart_core` 不应新增客户、供应商、合同、资金等业务事实归类规则。

### 2026-05-06 P0-7 第五轮落地

已执行：

- 新增 `delivery/product_identity.py`，统一 release/operator 产品身份解析：
  - `product_key = base.edition` 时直接解析 base 与 edition。
  - 传入 `platform.preview` 时解析为 `base_product_key = platform`、`edition_key = preview`。
  - 无参数时才走 legacy default base product。
- `ReleaseApprovalPolicyService`、`ReleaseAuditTrailService`、`ReleaseOperatorReadModelService` 统一使用 product identity resolver。
- `ReleaseOperatorReadModelService` 的可选产品列表从固定 `construction.standard/construction.preview` 改为跟随当前 base product：
  - `platform.preview` -> `platform.standard` / `platform.preview`
  - `construction.preview` -> `construction.standard` / `construction.preview`
- release approval 角色解析新增扩展 hook：
  - `smart_core_resolve_release_actor_role_codes`
  - construction group 解析仅保留为 legacy fallback。
- 补齐 release/delivery source authority：
  - `delivery_product_identity_resolver`
  - `delivery_engine_projection`
  - `release_approval_policy_projection`
  - `release_audit_trail_projection`
  - `release_operator_read_model_projection`
  - `release_operator_surface_projection`

边界结论：

- `smart_core/delivery/*` 是产品交付治理投影层，不是行业事实层。
- construction 默认策略仍作为 legacy fallback 存在，但可执行路径已经支持参数化 product identity。
- 后续应将 `DEFAULT_PRODUCT_POLICY` 的施工行业菜单/场景默认数据迁移为数据库 seed 或行业模块 profile。

### 2026-05-06 P0-8 第六轮落地

已执行：

- `ProductPolicyService` 的 fallback 读取统一经过 `_default_product_policy()`。
- `DEFAULT_PRODUCT_POLICY` 仍保留为 legacy fallback 数据，但不再是裸常量主路径。
- fallback policy 输出增加 `policy_source_authority`：
  - `legacy_default_product_policy_provider`
  - `projection_only = True`
  - `no_business_fact_authority = True`
- 新增扩展 hook：
  - `smart_core_build_default_product_policy`
  - 行业模块可通过 hook 替换默认产品策略。
- 非 construction 产品 fallback 已参数化：
  - `platform.preview` 会返回 `product_key = platform.preview`
  - `base_product_key = platform`
  - `edition_key = preview`
  - `label = Platform Preview`
- `scene_delivery_policy` source authority 补齐为 `scene_delivery_policy_projection`。
- `scene_delivery_policy` 默认 surface 统一为 `workspace_default_v1`。
- `construction_pm_v1` 保留为 legacy surface alias，运行时归一化为 `workspace_default_v1`。

边界结论：

- 产品策略 fallback、场景交付 surface 均已声明为投影/策略层，不承担行业业务事实。
- core 内剩余 construction 文本主要是 legacy fallback 数据、legacy alias、测试样例和向后兼容入口。
- 后续迁移动作应把 `DEFAULT_PRODUCT_POLICY` 迁入行业模块 seed/profile，并把 core fallback 降为最小空策略。

### 2026-05-06 P0-9 第七轮落地

已执行：

- `core/project_context.py` 从项目专属上下文降级为通用 `record_context_projection`。
- 现有函数名 `build_project_context_contract`、`selected_project_id_from_context` 等保留兼容。
- 默认模型 `project.project` 仅作为 legacy default model：
  - source authority 中声明 `legacy_default_model = project.project`
  - 本层 `no_business_fact_authority = True`
- 新增通用上下文模型解析：
  - 请求参数：`record_context_model` / `context_model` / `project_context_model`
  - 扩展 hook：`smart_core_resolve_record_context_config`
  - 配置项：`sc.record.context.model`
  - 最后才 fallback 到 legacy `project.project`
- `ProjectContextSearchHandler` source kind 从 `odoo_project_context_projection` 改为 `record_context_projection`。
- `system.init` 继续输出 `project_context` 兼容字段，但内部来源已经是 record context projection。

边界结论：

- `smart_core` 可以保留“当前记录上下文”能力。
- “项目”只是施工行业的默认上下文实例，不应作为 core 语义。
- 下一步应将前端和行业模块逐步从 `project_context` 命名迁移到 `record_context` / `business_context` 命名。

### 2026-05-06 P0-10 第八轮落地

已执行：

- `utils/reason_codes.py` 增加 `reason_code_metadata_registry` source authority。
- 付款/结算/资金类 reason code 常量保留兼容，但从主 `failure_meta_for_reason` 映射中拆出到 `legacy_business_reason_meta_mapping()`。
- legacy 业务 reason provider 声明：
  - `kind = legacy_business_reason_metadata_provider`
  - `projection_only = True`
  - `no_business_fact_authority = True`
  - `legacy_compatibility = True`
- `failure_meta_for_reason(P0_PAYMENT_*)` 仍返回原兼容行为，同时额外带 `source_authority`，说明该元数据来自 legacy business provider。
- 新增边界测试：reason registry 不得直接声明业务事实权威，付款类 reason metadata 必须标记 legacy provider。

边界结论：

- `smart_core` 可以保留通用 reason code registry。
- 付款、结算、资金等行业业务状态 reason 不应继续作为 core 主语义；当前仅为兼容 provider。
- 后续应将付款类 reason constants 和 suggested action 元数据迁入 `smart_construction_core`，core 只保留扩展注册/查询机制。

### 2026-05-06 P0-11 第九轮落地

已执行：

- `utils/contract_governance.py` 增加 `ui_contract_governance_projection` source authority。
- 行业专属治理规则增加 legacy profile source：
  - `legacy_industry_governance_profile`
  - `projection_only = True`
  - `no_business_fact_authority = True`
  - `legacy_compatibility = True`
- 付款申请列表治理、材料计划列表治理、tier review 列表动作过滤不改行为，但会在 `governance_diagnostics.legacy_industry_profiles` 中记录：
  - `payment.request.list`
  - `project.material.plan.list`
  - `tier.review.list`
- 默认 contract domain governance 已显式注册进 `apply_contract_governance` 管线，避免定义了治理入口但完整契约链路不执行。
- 付款申请列表治理测试增加诊断断言，证明该规则已被标记为 legacy industry profile。

边界结论：

- `smart_core` 的治理管线只能承担 UI 契约投影、裁剪、排序和兼容。
- 付款、材料、tier review 等行业专属 profile 当前保留兼容，但不再作为 core 通用治理语义。
- 后续应将这些 profile 迁入 `smart_construction_core` 的 governance override/provider。

### 2026-05-06 P0-12 第十轮落地

已执行：

- `controllers/platform_menu_api.py` 增加 `platform_menu_delivery_projection` source authority。
- 平台菜单的“业务配置管理员”判断从固定 `smart_construction_core.group_sc_cap_business_config_admin` 改为可配置来源：
  - extension hook：`smart_core_business_config_admin_group_xmlids`
  - 系统参数：`smart_core.business_config_admin_group_xmlids`
  - 最后才 fallback 到 legacy construction group。
- `system_init` 的行业扩展模块探测从固定 construction 模块列表改为可配置来源：
  - extension hook：`smart_core_industry_extension_module_names`
  - 系统参数：`smart_core.industry_extension_modules`
  - 最后才 fallback 到 legacy construction modules。
- 新增边界测试，证明菜单权限来源和 startup 行业模块探测都不再以 construction 作为唯一事实。

边界结论：

- `smart_core` 可以判断“是否有业务配置权限”和“是否进入最小平台模式”，但不能把施工模块/施工角色组作为核心事实。
- construction 组和模块名当前仅是兼容 fallback，应由行业模块通过 hook 或参数显式提供。

### 2026-05-06 P0-13 第十一轮落地

已执行：

- `contract_governance` 中用户列表面的模型级策略增加 legacy source：
  - `legacy_user_surface_model_policy`
  - `projection_only = True`
  - `no_business_fact_authority = True`
  - `legacy_compatibility = True`
- 现有行为不变：
  - `project.project` 仍保留禁删和打开记录时清理场景上下文的兼容策略。
  - `project.task`、`res.company`、`hr.department`、`res.users` 仍保留 delete-only 兼容策略。
- 这些模型级规则会进入 `governance_diagnostics.legacy_user_surface_model_policies`，不再隐性伪装为 core 通用策略。
- 新增边界测试，要求模型级 UI 策略必须声明 legacy source authority。

边界结论：

- `smart_core` 可以承载列表面批量动作、打开记录策略等 UI 投影规则。
- 针对具体业务模型的行为差异不是 core 事实，当前只能作为 legacy compatibility policy 存在。
- 后续应将这些模型策略迁入行业/垂直模块的 governance provider。

### 2026-05-06 P0-14 第十二轮落地

已执行：

- `utils/delete_policy.py` 增加 `unlink_policy_projection` source authority。
- 删除策略明确为默认拒绝、扩展或 handler allowlist 授权：
  - `extension_unlink_policy`
  - `handler_default_allowlist`
  - `odoo_access_control`
- `resolve_unlink_policy()` 返回的策略中增加 `source_authority`，说明策略层只决定是否开放 unlink 入口，实际删除事实仍由 Odoo ORM、ACL、record rule 承担。
- 新增边界测试，要求 unlink policy 不声明业务事实权威。

边界结论：

- `smart_core` 的删除能力边界是“代理 + 策略投影 + Odoo 权限校验”。
- 允许删除哪些业务模型不是 core 事实，应由扩展 hook 或 handler 显式 allowlist 给出。

### 2026-05-06 P0-15 第十三轮落地

已执行：

- `industry_orchestration_service_adapter._FallbackCostTrackingService` 从直接读取 `project.project` 改为纯 degraded projection：
  - source authority 不再包含 `project.project`
  - `no_business_fact_authority = True`
  - 缺失扩展服务时只回传传入 id 和降级原因，不再读取项目名称、编号等业务事实。
- `project_context` 的 scope 兼容函数增加 `legacy_project_scope_adapter` source authority。
- `apply_project_scope_domain()` 的 meta 增加：
  - `record_context_id`
  - `legacy_project_scope = True`
  - `source_authority = legacy_project_scope_adapter`
- `project_scope_denied_response()` 同时输出 `project_scope` 和 `record_scope`，保持旧客户端兼容并暴露通用语义。
- 新增边界测试，要求 degraded cost fallback 不得声明 `project.project` 权威，project scope 必须标记为 legacy adapter。

边界结论：

- 缺失行业扩展服务时，`smart_core` 只能返回降级契约，不能为了补体验去读取行业业务事实。
- `project_scope` 是历史兼容命名；core 的长期语义应迁移为 `record_scope` / `record_context`。

### 2026-05-06 P0-16 第十四轮落地

已执行：

- `handlers/api_data.py` 的项目范围拒绝响应补充 `record_scope`，与 `project_scope` 同源输出。
- `handlers/api_data_batch.py` 补齐 scope 语义：
  - 批量越界拒绝响应输出 `project_scope` 和 `record_scope`
  - 成功 data/meta/replay meta 同时输出 `project_scope` 和 `record_scope`
- 这些 scope meta 由 `apply_project_scope_domain()` 统一生成，已包含 `legacy_project_scope_adapter` source authority。

边界结论：

- 旧客户端继续读 `project_scope`。
- 新语义应读 `record_scope`，并通过 `source_authority.kind = legacy_project_scope_adapter` 判断这是历史项目上下文兼容路径。

### 2026-05-06 P0-17 第十五轮落地

已执行：

- 全口径补齐运行 handler 的 scope 输出：
  - `api_data` list/read/count/create/write/export_csv meta 增加 `record_scope`
  - `api_data_write` create/write 成功 data、meta、幂等 replay data/meta 增加 `record_scope`
  - `api_data_batch` 幂等 replay data 增加 `record_scope`
  - `api_data_unlink` 成功 data、meta、幂等 replay data/meta 增加 `record_scope`
  - `file_upload` / `file_download` 成功 meta 增加 `record_scope`
- `api_data_unlink` 的 scope 拒绝响应改用统一 `project_scope_denied_response()`，从而同时返回 `project_scope` 和 `record_scope`。

边界结论：

- 所有主要数据读写、批量写、删除、附件路径都已同时承载旧 `project_scope` 与新 `record_scope`。
- `project_scope` 仅为历史兼容字段；新消费者应按 `record_scope.source_authority.kind = legacy_project_scope_adapter` 识别其来源边界。

### 2026-05-06 P0-18 第十六轮落地

已执行：

- `workspace_home` 首页指标中前端可见的 `biz.project_scope` 改为 `biz.record_scope`。
- 为兼容旧前端/诊断保留 `legacy_key = biz.project_scope`。
- 新增测试，要求首页业务范围指标使用 record scope 主 key，并显式保留 legacy alias。

边界结论：

- 首页指标表达的是“当前账号可进入的业务场景覆盖范围”，不是项目业务事实。
- `project_scope` 不应继续作为 core 主语义出现在新契约 key 中。

### 2026-05-06 P0-19 第十七轮落地

已执行：

- `release_navigation_contract_builder` 增加 `release_navigation_projection` source authority。
- release navigation builder 优先消费 `delivery_engine_v1.nav`，不再在 system init 主路径中执行 FR-1 到 FR-5 的硬编码导航。
- 原 FR-1/FR-5 等硬编码发布导航保留为 `legacy_release_navigation_fallback`，仅在没有 delivery engine payload 时使用。
- `system_init` 中 release navigation builder 的调用改到 delivery engine 之后，诊断记录：
  - `builder_source`
  - `builder_contract_version`
  - `builder_source_authority`
- 新增边界测试，要求 release navigation 优先使用 delivery engine payload。

边界结论：

- release navigation 是交付产品策略的投影，不应由 core 单独固化施工 FR 导航。
- FR-1 到 FR-5 当前只作为 legacy fallback 存在；主路径由 `delivery_product_policy_projection` 驱动。

### 2026-05-06 P0-20 第十八轮落地

已执行：

- `ProductPolicyService` 的缺省策略拆成两层：
  - construction base product 继续使用 `legacy_default_product_policy_provider`
  - 非 construction base product 使用 `minimal_default_product_policy_provider`
- 非 construction 缺失数据库 policy / extension hook 时，返回最小通用 policy：
  - 不携带 FR-1 到 FR-5 菜单
  - 不携带 project/payment/settlement/cost 场景
  - 不携带 settlement scene binding
- `_fallback_stable_policy()` 对非 construction base product 也会返回最小通用 stable policy，不再把 construction 默认菜单改名后复用。
- 新增边界测试，要求 `platform.standard` 缺失策略时不带 construction/settlement 默认内容。

边界结论：

- construction 默认 policy 只能作为 legacy compatibility fallback。
- `smart_core` 对未知/新产品线的默认行为应是空的、可重建的交付投影，而不是套用施工行业事实。

### 2026-05-06 P0-21 第十九轮落地

已执行：

- `DeliveryEngine` 输出补充 product policy 来源诊断：
  - `product_policy.policy_source_authority`
  - `product_policy.policy_source_kind`
  - `product_policy.policy_empty`
  - `product_policy.policy_empty_reason`
- `meta` 同步输出：
  - `policy_source_kind`
  - `policy_empty`
  - `policy_empty_reason`
- 非 construction 最小默认策略导致空菜单/空场景时，明确标记 `policy_empty_reason = MINIMAL_DEFAULT_PRODUCT_POLICY`。
- 新增边界测试，要求 `platform.standard` 的 delivery payload 显示最小策略来源和空策略原因。

边界结论：

- 空导航不是异常；对未知产品线而言，这是 core 最小默认投影的预期结果。
- 前端/诊断应读取 `policy_source_kind` 和 `policy_empty_reason`，而不是把空菜单误判为数据缺失。

### 2026-05-06 P0-22 第二十轮落地

已执行：

- `ReleaseOperatorReadModelService` 的默认 base product 从固定 construction 改为可配置：
  - 系统参数：`smart_core.release_operator.default_base_product_key`
  - 未配置时才 fallback 到 legacy `construction`
- release operator read model 的 `identity` 增加来源诊断：
  - `source`
  - `requested_product_key`
  - `default_base_product_key`
  - `default_base_source`
  - `source_authority = delivery_product_identity_resolver`
- 新增测试，证明 release operator 在未传 product key 时可通过配置默认到 `platform.standard`。

边界结论：

- release operator surface 可以保留默认产品入口，但默认 base product 不能硬编码为施工行业。
- construction 仅作为 legacy fallback；部署/行业模块应通过配置显式指定默认产品线。

### 2026-05-06 P0-23 第二十一轮落地

已执行：

- `ReleaseApprovalPolicyService` 增加 `extension_role_resolver` source authority。
- 新增 `resolve_actor_role_context()`，在不破坏 `resolve_actor_role_codes()` 返回类型的前提下输出：
  - `actor_role_codes`
  - `role_source`
  - `source_authority`
  - `legacy_role_source_authority`
- `can_execute()` / `can_approve()` 诊断中增加 `role_context`。
- `ReleaseOperatorReadModelService` 的 promote/rollback action 和 read model 根部输出 actor role context。
- 新增边界测试，要求 construction role group fallback 显式标记为 legacy source。

边界结论：

- release 审批策略可以读取角色，但施工角色组映射不是 core 事实。
- 后续应由行业模块通过 `smart_core_resolve_release_actor_role_codes` hook 提供角色，core 中 construction group fallback 只保留兼容。

### 2026-05-06 P0-24 第二十二轮落地

已执行：

- `scene_contract_builder` 增加 `release_surface_scene_contract_projection` source authority。
- 所有 `scene_contract_standard_v1.governance` 输出补充：
  - `source_authority`
  - `no_business_fact_authority`
- FR-1 到 FR-5 默认产品标题映射继续保留兼容，但当该映射被实际使用时，合约治理区写入：
  - `legacy_product_title_source_authority.kind = legacy_release_product_title_projection`
- 补齐测试，要求场景合约构建器声明投影边界，并要求 FR 默认标题不能无来源进入核心合约。
- 同步修正旧测试：非 construction 缺失产品策略应返回 `minimal_default_product_policy_provider`，不能回落到 construction 默认策略。

边界结论：

- 场景合约构建器只负责把 delivery/runtime/page contract 投影成前端可消费合约。
- FR 产品标题不是核心事实源；它只能作为 legacy released product key 的展示兼容投影。

### 2026-05-06 P0-25 第二十三轮落地

已执行：

- `workspace_home_contract_builder` 增加 `legacy_workspace_keyword_policy_projection` source authority。
- `source_authority_contract()` 明确声明首页关键词策略是 legacy workspace projection policy。
- `build_workspace_home_contract().diagnostics.keyword_policy` 输出：
  - `source_authority`
  - `overrides_present`
  - `purpose = workspace_projection_ranking_and_route_hint`
- 保留现有 payment/settlement/cost/risk 等关键词启发式行为，但明确它只服务首页排序、紧急度和路由 hint。
- 补齐测试，要求关键词策略不能被当作业务事实源。

边界结论：

- workspace home 可以根据关键词做 UI 投影排序和入口推荐。
- 关键词策略不能参与客户/供应商、合同、资金或项目事实归类；事实归类必须来自合同事实或资金事实等业务源。

### 2026-05-06 P0-26 第二十四轮落地

已执行：

- `release_navigation_contract_builder` 的 legacy fallback 叶子节点补充来源标记：
  - `meta.source_authority.kind = legacy_release_navigation_fallback`
  - `meta.legacy_compatibility = true`
- delivery engine 主路径不变；只有 fallback 构造出的 FR/my_work 导航节点携带该 legacy 标记。
- 新增边界测试，要求 fallback nav leaf 不能无来源进入发布导航树。

边界结论：

- release navigation 主事实来源应优先是 `delivery_engine_v1.nav`。
- FR fallback 导航树只承担兼容展示，不能被当作产品发布事实或行业事实源。

### 2026-05-06 P0-27 第二十五轮落地

已执行：

- `scene_delivery_policy` 增加 `legacy_scene_surface_alias_projection` source authority。
- `source_authority_contract()` 明确声明 legacy surface alias 来源。
- `resolve_delivery_policy_runtime()` 输出：
  - `requested_surface`
  - `legacy_surface_alias`
- `filter_delivery_scenes().meta` 输出：
  - `requested_surface`
  - `legacy_surface_alias`
- `construction_pm_v1 -> workspace_default_v1` 兼容行为不变，但调用方可以看到这是 legacy alias 归一化。

边界结论：

- scene delivery surface 是发布/导航投影策略，不是业务事实源。
- construction surface alias 只能作为历史输入兼容；实际 surface policy 应收敛到通用 workspace policy 或由扩展 hook/file 显式提供。

### 2026-05-06 P0-28 第二十六轮落地

已执行：

- `page_contracts_builder` 增加 `page_contract_projection` source authority。
- `build_page_contracts()` 根 payload 输出：
  - `source_authority`
  - `diagnostics.legacy_page_copy_source_authority`
  - `diagnostics.page_profile_overrides_present`
- 内置页面文案中保留的项目/付款/资金等行业 copy 被标记为：
  - `legacy_industry_page_copy_projection`
- 新增直接边界测试，要求页面合约构建器不声明业务事实权威。

边界结论：

- page contracts 是前端页面投影，不是业务事实源。
- 内置行业文案只作为兼容 copy fallback；事实归类、客户/供应商语义、合同/资金状态不能从这些文案或关键词推断。

### 2026-05-06 P0-29 第二十七轮落地

已执行：

- `product_policy_service` 增加 `legacy_default_product_policy_node_projection` source authority。
- construction `DEFAULT_PRODUCT_POLICY` 作为 legacy fallback 返回时，节点级补充：
  - `menu_groups[].policy_node_source_authority`
  - `menu_groups[].menus[].policy_node_source_authority`
  - `scenes[].policy_node_source_authority`
  - `capabilities[].policy_node_source_authority`
- `default_policy_source_authority_contract()` 增加 `legacy_policy_node_source`。
- 新增测试，要求默认 FR/payment/settlement 节点不可无来源进入交付策略。

边界结论：

- construction 默认产品策略只能是 legacy fallback。
- FR、payment、settlement 等节点级信息不能被下游当作 core 事实；正式产品策略应来自 `sc.product.policy`、snapshot 或扩展 hook。

### 2026-05-06 P0-30 第二十八轮落地

已执行：

- `MenuDeliveryConvergenceService` 增加 `menu_delivery_convergence_projection` source authority。
- 行业菜单词表策略标记为：
  - `legacy_industry_menu_token_policy`
- `apply()` 返回 report 增加：
  - `source_authority`
  - `legacy_token_policy_source_authority`
- 保持当前菜单过滤/重命名行为不变，但菜单展示规则的行业词表来源已经可审计。

边界结论：

- 菜单收敛服务只做系统菜单视图投影治理，不是客户/供应商、合同、资金或项目事实源。
- `智能施工/项目/结算/付款` 等词表只能作为 legacy 菜单兼容策略；后续通用菜单治理应由产品策略或扩展配置显式提供。

### 2026-05-06 P0-31 第二十九轮落地

已执行：

- `SystemInitPayloadBuilder` 增加 `system_init_startup_payload_projection` source authority。
- `build_startup_surface()` 输出的 `init_meta` 增加：
  - `source_authority`
- 启动载荷裁剪、默认路由、scene subset、page contract preload 等规则明确为 system init 投影层能力。
- 新增测试，要求启动载荷构建器不声明业务事实权威。

边界结论：

- system init payload 是运行时启动载荷投影，不是业务事实源。
- 它可以携带 delivery/page/scene/nav 的最小启动视图，但不能决定客户/供应商、合同、资金或项目事实。

### 2026-05-06 P0-32 第三十轮落地

已执行：

- `runtime_page_contract_builder` 增加 `runtime_page_contract_projection` source authority。
- `build_runtime_page_contracts()` 根 payload 增加：
  - `runtime_source_authority`
- 每个页面的 `page_orchestration_v1.meta` 增加：
  - `runtime_source_authority`
- 新增直接边界测试，要求 runtime page contract builder 只声明页面运行时投影能力。

边界结论：

- runtime page contract builder 负责把 page contract 变成运行时消费形态，并补 role context / semantic bridge。
- 它不拥有页面文案、业务事实或客户/供应商事实；上游 page/source authority 必须继续可追踪。

### 2026-05-06 P0-33 第三十一轮落地

已执行：

- `BaseSceneEntryOrchestrator` 增加 `legacy_scene_entry_copy_projection` source authority。
- `source_authority_contract()` 声明 `legacy_scene_copy_source`。
- `build_entry()` / `build_runtime_block()` 输出增加：
  - `legacy_scene_copy_source_authority`
- 项目/付款/结算/成本等 scene label、fallback text、block title、resolve_title 仍保留兼容，但来源明确为 legacy scene entry copy。

边界结论：

- scene entry orchestrator 是运行时场景入口投影 adapter。
- 场景标题与 block copy 不是业务事实源；实际业务事实只允许来自 delegated service 的 source authority。

### 2026-05-06 P0-34 第三十二轮落地

已执行：

- `product_identity` 增加 `legacy_default_base_product_projection` source authority。
- `source_authority_contract()` 增加 `legacy_default_base_source`。
- `resolve_product_identity()` 在无显式 product/base 输入、走 legacy default construction 时输出：
  - `legacy_default_base_source_authority`
- 显式 `platform.preview` 等 product key 不携带 legacy default base source。

边界结论：

- product identity resolver 可以解析默认产品身份，但默认 construction base 只能是 legacy fallback。
- 调用方不能把默认 construction 当作 core 产品事实；应通过请求参数或配置显式传入 base/product。

### 2026-05-06 P0-35 第三十三轮落地

已执行：

- `EditionReleaseSnapshotService` 增加 `edition_release_snapshot_projection` source authority。
- `build_freeze_surface()` 根 payload 和 `runtime_meta` 增加：
  - `source_authority`
- 默认 role fallback `pm` 标记为：
  - `legacy_release_snapshot_default_role_projection`
- 修复直接访问 `sc.product.policy` 的越界问题：模型未注册时不再 KeyError，沿用 product policy/delivery engine 的降级路径。

边界结论：

- edition release snapshot 是发布快照投影，不拥有产品/角色/业务事实。
- 产品策略事实来自 `sc.product.policy` 或 product policy provider；默认 PM 角色只能作为 legacy fallback。

### 2026-05-06 P0-36 第三十四轮落地

已执行：

- `EditionReleaseSnapshotPromotionService` 增加 `edition_release_snapshot_promotion_proxy` source authority。
- `source_authority_contract()` 明确：
  - `write_proxy = true`
  - `no_business_fact_authority = true`
- promote / release / supersede 返回 payload 增加：
  - `promotion_source_authority`
- 补充边界测试，要求 promotion service 是 snapshot 状态迁移代理，不是业务事实源。

边界结论：

- promotion service 可以写入 release snapshot 状态机。
- 它只能代理 `sc.edition.release.snapshot` 状态迁移，不能创造产品、角色或业务事实。

### 2026-05-06 P0-37 第三十五轮落地

已执行：

- `SceneSnapshotService` 增加 `scene_snapshot_projection` source authority。
- `SceneService` 增加 `delivery_scene_projection` source authority。
- `resolve_snapshot_with_diagnostics()` 在 `sc.scene.snapshot` 未注册时不再 KeyError，返回：
  - `snapshot_fallback_reason = SNAPSHOT_MODEL_NOT_AVAILABLE`
  - `source_authority.kind = scene_snapshot_projection`
- `SceneService.build_entries()` 的每个 delivery scene entry 增加 `source_authority`。

边界结论：

- scene snapshot 是场景合约缓存/投影，不是业务事实源。
- delivery scene 构建可以使用 snapshot，但 snapshot 模型缺失时必须诊断降级，不能阻断通用 delivery engine。

### 2026-05-06 P0-38 第三十六轮落地

已执行：

- `MenuFactService` 增加 `odoo_menu_fact_projection` source authority。
- `MenuFactSnapshot` 输出增加：
  - `source_authority`
- `audit_menu_facts()` 输出增加菜单事实来源。
- `MenuService` 增加 `delivery_menu_projection` source authority。
- delivery nav root、describe_nav、叶子节点 meta 透传菜单投影来源。
- `DeliveryEngine.meta` 增加 `nav_source_authority`。
- `/api/menu/tree` 与 `/api/menu/navigation` 响应 meta 增加：
  - `source_authority`
  - `menu_fact_source_authority`
- 补充 native alignment 边界测试，要求菜单事实层和菜单投递层均不声明业务事实权威。

边界结论：

- 菜单事实只来自 Odoo 原生 `ir.ui.menu` / `ir.actions` / groups 注册表。
- 菜单投递服务只负责把菜单事实、产品策略和收敛规则投影为系统菜单视图。
- 菜单同步/清理不能依据 construction、客户/供应商或场景治理语义自行裁剪业务事实；业务事实仍必须由上游事实源决定。

### 2026-05-06 P0-39 第三十七轮落地

已执行：

- `capability_provider` 增加 `capability_startup_surface_projection` source authority。
- extension capability hook 与 `sc.capability` 返回能力项统一补充 `source_authority`。
- `CapabilityService` 增加 `delivery_capability_projection` source authority。
- delivery capability entry 增加：
  - `source_authority`
  - `runtime_source_authority`
- `DeliveryEngine.meta` 增加：
  - `capability_source_authority`
- 补充 native alignment 边界测试，要求 capability startup surface 与 delivery capability projection 均不声明业务事实权威。

边界结论：

- capability 是权限/能力配置投影，不是客户、供应商、合同、资金或施工业务事实。
- startup capability provider 的事实来源只允许是扩展 hook 或 `sc.capability` 配置。
- DeliveryEngine 只能把产品策略能力与启动能力配置合并为交付面，不能基于 capability 自行创造业务事实分类。

### 2026-05-06 P0-40 第三十八轮落地

已执行：

- `intent_permission` 增加 `odoo_native_permission_projection` source authority。
- `PermissionCheckHandler` 增加 `source_authority_contract()`。
- permission.check meta 增加：
  - `source_authority`
- `intent_permission` 与 `PermissionCheckHandler` 的 capability 查找统一改为安全查找：
  - `sc.capability` 不存在时返回空能力，不再 KeyError。
- 补充 native alignment 边界测试，要求权限投影不声明业务事实权威。

边界结论：

- permission 层只判断 Odoo ACL、record rule、菜单/动作可见性、entitlement 与 capability flag。
- permission 层不是业务事实源；不能用权限、能力或 entitlement 推导客户/供应商、合同事实或资金事实。
- capability 模型缺失属于配置能力不可用，不能让 core 启动或通用权限检查因行业模块缺失而崩溃。

### 2026-05-06 P0-41 第三十九轮落地

已执行：

- `scene_provider` 增加 `scene_runtime_provider_projection` source authority。
- `AutoDegradeEngine` 增加 `scene_auto_degrade_governance_proxy` source authority。
- auto-degrade evaluate 返回增加：
  - `source_authority`
- `SceneHealthHandler` 增加 `source_authority_contract()`，响应 meta 增加 `source_authority`。
- `scene_package` / `scene_governance` handler 的 source contract 补齐：
  - `projection_only`
  - `write_proxy`（治理变更）
  - `no_business_fact_authority`
- 补充 native alignment 边界测试，要求 scene runtime provider、auto-degrade、scene health 均不声明业务事实权威。

边界结论：

- scene provider 只合并场景注册表、场景合约导出、配置参数、菜单/动作/capability 的运行时入口信息。
- auto-degrade 是场景治理写代理，只能根据 scene diagnostics 写 rollback/config/log，不拥有业务事实。
- scene health/package/governance 是交付治理面，不得基于场景状态改变客户/供应商、合同或资金事实。

### 2026-05-06 P0-42 第四十轮落地

已执行：

- `AppCatalogHandler` / `AppNavHandler` / `AppOpenHandler` 统一增加 app shell source authority。
- app shell 响应 meta 增加：
  - `source_authority`
- `ScenePackagesInstalledHandler` 增加 `source_authority_contract()`。
- scene packages installed 响应 meta 增加：
  - `source_authority`
- 补充 native alignment 边界测试，要求 app catalog/nav/open 与 package registry 均不声明业务事实权威。

边界结论：

- app catalog/nav/open 是前端应用壳投影，只负责把 scene delivery 入口整理给客户端。
- scene package registry 是包安装状态投影，不是业务事实源。
- 这些入口不能根据应用、菜单、场景或包状态推导客户/供应商、合同、资金或任何业务事实分类。

### 2026-05-06 P0-43 第四十一轮落地

已执行：

- `MetaDescribeHandler` / `LoadMetadataHandler` 增加 `odoo_fields_get_projection` source authority。
- `MetaIntentCatalogHandler` 增加 `intent_delivery_catalog_projection` source authority。
- `SearchFavoriteSetHandler` 增加 `odoo_filter_write_proxy` source authority。
- `UserViewPreferenceGetHandler` / `UserViewPreferenceSetHandler` 增加 `ui_only_user_preference` source authority。
- `TerminalShellV2Handler` 增加 `terminal_shell_contract_v2` source authority。
- `LoginHandler` / `LogoutHandler` 增加 `odoo_auth_session_proxy` source authority。
- `VersionedDataHandlerV21` 继承 versioned handler source authority。
- 相关响应 meta 增加：
  - `source_authority`
- 补充 native alignment 边界测试，要求这些通用入口均不声明业务事实权威。

边界结论：

- metadata / intent catalog 是只读元数据投影，不拥有业务事实。
- search favorite / user view preference 是 UI 配置写代理，不得改写业务事实。
- login / logout 是认证会话代理，只处理用户、组、公司与 token，不得推导客户/供应商或资金事实。
- terminal shell 是 app catalog/nav/open/ui contract 的聚合投影，不得越界成为业务事实源。

### 2026-05-06 P0-44 第四十二轮落地

已执行：

- `FileUploadHandler` 增加 `odoo_attachment_upload_proxy` source authority。
- `FileDownloadHandler` 增加 `odoo_attachment_download_projection` source authority。
- `ChatterPostHandler` 增加 `odoo_collaboration_message_write_proxy` source authority。
- `ChatterActivityScheduleHandler` 增加 `odoo_collaboration_activity_write_proxy` source authority。
- `ChatterTimelineHandler` 增加 `odoo_collaboration_timeline_projection` source authority。
- `SessionBootstrapHandler` 增加 `dev_test_auth_bootstrap_proxy` source authority。
- `UiContractV2Handler` 增加 `unified_page_contract_v2` source authority。
- 文件/协作响应保留 legacy string source authority，同时新增结构化 `source_authority`。
- 补充 native alignment 边界测试，要求文件、协作、bootstrap、ui contract v2 均不声明业务事实权威。

边界结论：

- file upload/download 是附件读写代理，只代理 `ir.attachment` 与目标记录 ACL/rule/scope，不拥有业务事实。
- chatter message/activity/timeline 是协作事实投影/写代理，不得推导客户/供应商、合同或资金事实。
- session bootstrap 仅限 dev/test 认证令牌代理。
- ui contract v2 是页面契约聚合投影，不能成为业务事实源。

### 2026-05-06 P0-45 第四十三轮落地

已执行：

- `app_config_engine` 原生配置投影统一补齐 `no_business_fact_authority`：
  - `app.model.config`
  - `app.action.config`
  - `app.menu.config`
  - `app.report.config`
  - `app.validator.config`
  - `app.permission.config`
  - `app.workflow.config`
  - `app.search.config`
  - `app.view.config`
- `AppActionGateway` 增加 `odoo_runtime_action_gateway` source authority。
- `ScUserViewPreference` 增加 `ui_only_user_preference` source authority。
- `res.users` 扩展增加 `odoo_auth_session_extension` source authority。
- `ui_base_contract_asset` invalidation triggers 增加结构化 source authority。
- `ContractSchemaMixin` 增加 `ui_contract_sanitizer` source authority。
- 修正 native alignment 测试中菜单配置模型引用为实际注册名 `app.menu.config`。

边界结论：

- app_config_engine 只缓存/投影 Odoo 原生模型、字段、视图、动作、菜单、权限、报表、搜索、工作流配置。
- action gateway 是运行时方法/onchange 代理，不拥有业务事实。
- user preference、asset trigger、contract sanitizer 都是 UI/契约基础设施，不得推导客户/供应商、合同或资金事实。

### 2026-05-06 P0-46 第四十四轮落地

已执行：

- `extension_loader` 增加 `smart_core_extension_loader` source authority。
- `extension_hooks` 增加 `smart_core_extension_hook_resolver` source authority。
- `SceneChannelPolicy` 增加 `scene_channel_policy_projection` source authority。
- `ui_base_contract_asset_event_queue` 增加 `ui_base_contract_asset_event_queue` source authority。
- `ui_base_contract_asset_repository` 增加 `ui_base_contract_asset_repository` source authority。
- `system_init_dictionary_data_helper` 增加 `system_init_dictionary_data_projection` source authority。
- `IntentSurfaceBuilder` 增加 `intent_surface_projection` source authority。
- UI base contract asset 队列、仓库与字典 startup 输出增加结构化 `source_authority`。
- 补充 native alignment 边界测试，要求 runtime infrastructure 均不声明业务事实权威，资产队列/仓库只能作为 UI 契约缓存写代理。

边界结论：

- extension loader/hooks 只解析配置与扩展 hook，不拥有客户、供应商、合同或资金事实。
- scene channel policy 只根据 request/config/environment 选择场景通道，不得替代事实源治理。
- UI base asset event queue/repository 是 UI 契约缓存基础设施和写代理，不是业务事实写入层。
- dictionary startup helper 是字典数据投影，不能基于字典枚举推导业务事实归属。
- intent surface builder 是 handler/permission surface 投影，只表达入口能力，不表达客户/供应商事实分类。

### 2026-05-06 P0-47 第四十五轮落地

已执行：

- `ContractService` 增加 `app_config_contract_service_projection` source authority。
- `ActionDispatcher` 增加 `app_config_action_dispatch_proxy` source authority。
- `MenuDispatcher` 增加 `app_config_menu_dispatch_projection` source authority。
- `NavDispatcher` 增加 `app_config_nav_dispatch_projection` source authority。
- `ActionResolver` 增加 `odoo_action_resolution_projection` source authority。
- `PageAssembler` 增加 `app_config_page_contract_projection` source authority。
- `ClientUrlReportAssembler` 增加 `client_url_report_contract_projection` source authority。
- `ContractService` HTTP meta、`NavDispatcher` meta、`PageAssembler` data 输出结构化 `source_authority`。
- 补充 native alignment 边界测试，要求 app_config 服务层均不声明业务事实权威。

边界结论：

- app_config_engine 服务层只负责 payload 解析、subject 分发、Odoo 原生动作/菜单/视图解析、页面契约装配和契约治理。
- action dispatcher/resolver 可以代理执行 Odoo 方法、onchange 或 server action 探测，但只作为运行时代理，不拥有业务事实。
- menu/nav dispatcher 只投影 `ir.ui.menu`、动作、组和配置缓存，不得依据菜单/场景/配置推导客户或供应商。
- page assembler 聚合模型、视图、搜索、权限、按钮、报表、工作流和校验契约；它可以读取业务模型数据用于首屏展示，但不能改变客户/供应商/合同/资金事实归类。
- client/url/report assembler 只装配非数据页契约，不参与业务事实治理。

### 2026-05-06 P0-48 第四十六轮落地

已执行：

- `NativeParseService` 增加 `odoo_native_view_parse_coordinator` source authority。
- `ParseFallbackService` 增加 `odoo_view_parse_fallback_coordinator` source authority。
- `ContractGovernanceFilterService` 增加 `ui_contract_runtime_governance_filter` source authority。
- `ContractNormalizer` 增加 `ui_contract_shape_normalizer` source authority。
- `app.view.parser` 增加 `odoo_view_contract_parser_projection` source authority。
- view parser base / http / payload / misc / view_utils 补齐结构化 source authority。
- legacy `smart_core.view` 解析器补齐 legacy projection source authority。
- 补充 native alignment 边界测试，要求视图解析、契约规范化、HTTP/payload 工具和 legacy 视图解析器均不声明业务事实权威。

边界结论：

- 视图解析只解析 `ir.ui.view`、`fields_get/get_view`、toolbar、modifiers、布局和按钮结构。
- contract normalizer 只做结构兜底、类型纠偏、裁剪和安全默认值，不重写业务含义。
- governance filter 只依据用户组、ACL 和已解析契约做运行时 UI 裁剪。
- HTTP/payload/misc/view_utils 都是契约输入、ETag、domain/context 和列表列解析工具。
- legacy view parser 虽然名称里有 semantic，但只能表达 UI 结构语义，不得推导客户/供应商、合同或资金事实。

### 2026-05-06 P0-49 第四十七轮落地

已执行：

- 页面、运行时页面、场景、scene ready、system init 相关 `semantic_bridge` 模块统一补齐 source authority。
- `orchestration_semantics` 增加 `ui_orchestration_semantics_registry` source authority。
- `SceneRuntimeOrchestrator` 增加 `scene_runtime_orchestration_projection` source authority。
- `SceneDiagnosticsBuilder` 增加 `scene_diagnostics_projection` source authority。
- `scene_governance_payload_builder` 增加 `scene_governance_payload_projection` source authority。
- `SceneDriftEngine` 增加 `scene_drift_health_projection` source authority。
- `IdentityResolver` 增加 `role_identity_surface_projection` source authority。
- `system_init_extension_fact_merger` 增加 `system_init_extension_fact_contribution_merger` source authority，并显式标记 `delegates_business_fact_authority=True`。
- 补充 native alignment 边界测试，覆盖 semantic bridge、scene runtime、identity、drift 和 extension fact merger。

边界结论：

- 所有 `semantic_bridge` 只在 UI/页面/场景契约之间搬运和映射 parser/view/page/runtime 语义。
- orchestration semantics 是静态 UI 编排枚举注册表，不是业务分类规则。
- scene runtime、diagnostics、governance payload、drift health 都只治理场景投影健康状态。
- IdentityResolver 只解析用户角色、入口场景和菜单候选，不得推导客户/供应商、合同或资金事实。
- extension fact merger 允许承载扩展模块贡献的事实片段，但 smart_core 只合并和转交，不解释这些事实，也不取得业务事实权威。

### 2026-05-06 P0-50 第四十八轮落地

已执行：

- `IntentDispatcher` 增加 `http_intent_dispatch_controller` source authority。
- `BaseIntentHandler` 增加 `intent_handler_runtime_base` source authority。
- `RequestContext` 增加 `http_request_context_projection` source authority。
- `intent_router` 增加 `intent_router_runtime_dispatch` source authority。
- `middlewares` 增加 `intent_middleware_runtime_pipeline` source authority。
- `trace` 增加 `request_trace_id_projection` source authority。
- `IntentExecutionResult` 增加 `intent_execution_result_envelope` source authority。
- `exceptions` 增加 `intent_error_envelope_registry` source authority。
- `hash_utils` 增加 `stable_hash_utility` source authority。
- `idempotency` 增加 `idempotency_audit_replay_projection` source authority。
- `response_builder` 增加 `http_json_response_builder` source authority。
- 补充 native alignment 边界测试，覆盖 HTTP 意图入口、handler 基类、router、middleware、trace、错误 envelope、执行结果、hash、幂等与响应工具。

边界结论：

- HTTP intent controller、router、handler base 和 middleware 是请求分发、权限前置、事务提交、响应 envelope 与运行时代理层。
- trace、hash、exceptions、execution result、response builder 是技术 envelope 工具，不读取或解释业务事实。
- idempotency 只基于 audit log、request id、fingerprint 做重放/冲突判断，不依据资金、合同或往来单位语义分类。
- 这条入口链路可以代理写请求，但事实权威必须留在被调用业务模型/扩展模块，smart_core 不取得客户/供应商事实解释权。

### 2026-05-06 P0-51 第四十九轮落地

已执行：

- `NavTreeCleaner` / `OdooNavAdapter` 补齐导航投影 source authority。
- `action_target_schema` / `native_view_contract_projection` / `page_orchestration_data_provider` 补齐 UI target 与页面编排投影 source authority。
- `scene_dsl_compiler` / `scene_merge_resolver` / `scene_nav_contract_builder` 补齐场景 DSL、merge 和 nav contract 投影 source authority。
- `SceneNormalizer` / `CapabilitySurfaceEngine` 补齐场景规范化与能力摘要投影 source authority。
- Unified Page Contract Lite 与 V2 系列模块补齐结构化 source authority。
- `ui_base_contract_adapter` / `ui_base_contract_asset_producer` / `ui_base_contract_canonicalizer` 补齐 UI base contract source authority。
- `ContractAssembler` 补齐 system init meta assembler source authority。
- 补充 native alignment 边界测试，覆盖导航、场景治理、unified page contract 和 UI base contract 构造链路。

边界结论：

- 导航 adapter/cleaner 只清洗菜单树、组 xmlid 和 scene key 投影。
- action target/schema、scene nav、scene DSL、merge resolver 只描述 UI 入口、页面布局、场景契约和 provider/policy 合并。
- Unified Page Contract Lite/V2 只做跨端页面契约、patch、状态、数据源和客户端裁剪投影。
- UI base contract adapter/producer/canonicalizer 只构造、规范化并缓存 UI 契约；producer 可以写 UI cache，但不是业务事实写入层。
- 这些模块不得依据场景、菜单、视图、页面或能力摘要推导客户/供应商、合同或资金事实。

### 2026-05-06 P0-52 第五十轮落地

已执行：

- `SystemInitComponentsFactory` / `SystemInitRuntimeContext` / `SystemInitSurfaceContext` / `SystemInitSceneRuntimeSurfaceContext` 补齐 system init 运行时组件与上下文 carrier source authority。
- `SystemInitDiagnosticsHelper` 补齐 system init diagnostics projection source authority。
- `SystemInitIdentityPayload` 补齐身份 payload 投影 source authority，并显式标记 `identity_surface_only=True`。
- `security.auth` 补齐 `jwt_auth_session_proxy` source authority，并标记为认证/session 写代理，不是业务事实源。
- `MenuTargetInterpreterService` 补齐菜单事实到导航目标解释 source authority，并显式标记 `facts_remain_unchanged=True`。
- `release_operator_contract_registry` / `release_operator_contract_versions` 补齐 release operator 静态契约元数据 source authority。
- `ui.dynamic.config` 补齐 UI overlay source authority，并修复 `smart_core.__init__` 未导入 `model` 包导致模型未进入 Odoo registry 的问题。
- 补充 native alignment 边界测试，覆盖 system init carrier、认证、菜单目标解释、release contract registry/version 和 UI overlay 配置。

边界结论：

- system init 上下文/工厂只承载请求参数、场景运行时依赖、能力摘要、身份 surface 和契约装配组件。
- 认证层只校验 JWT、Odoo session 和 `res.users` 身份，不得参与客户/供应商、个人/企业、合同或资金事实归类。
- 菜单目标解释只把 `odoo_menu_fact_projection` 映射为 scene/action/native/url/directory 导航目标；原始菜单事实不被改写。
- release operator registry/version 是冻结契约元数据，不包含也不解释业务事实。
- `ui.dynamic.config` 是按 view/company/user 维度的 UI 覆盖配置，只能影响界面契约，不得改变业务事实或作为客户/供应商来源。

### 2026-05-06 P0-53 第五十一轮落地

已执行：

- `SystemInitNavRequestBuilder` 补齐 system init nav request projection source authority。
- `SystemInitPreloadBuilder` 补齐 startup preload contract projection source authority。
- `SystemInitResponseMetaBuilder` 补齐 system init response meta projection source authority。
- `SystemInitSurfaceBuilder` 补齐 system init surface projection builder source authority。
- `SystemInitSceneRuntimeSurfaceBuilder` 补齐 scene runtime surface projection builder source authority。
- `RequestDiagnosticsCollector` 补齐 request diagnostics projection source authority。
- `command_registry` 补齐 legacy command registry projection source authority。
- `delivery_menu_defaults` 补齐 delivery menu default projection source authority，并把默认来源写入 synthetic menu meta。
- `delivery_capability_entry_defaults` 补齐 capability entry default projection source authority，并把默认来源写入 entry payload。
- `scene_ready_contract_builder` 补齐 scene ready contract projection source authority，并写入 contract meta。
- 扩展 native alignment 边界测试，覆盖 system init builder、诊断、legacy command registry、delivery 默认菜单/能力 entry 和 scene ready contract。

边界结论：

- system init nav/preload/meta/surface builder 只构建启动请求、预加载契约、响应 envelope 和运行时 surface。
- request diagnostics 只读取 header、params、env、用户身份用于诊断，不解释合同、资金或伙伴事实。
- legacy command registry 只是命令类注册表兼容层，不是客户/供应商事实来源。
- delivery 默认菜单与能力 entry 只生成 synthetic navigation/capability 展示节点；这些默认节点不得成为业务归类依据。
- scene ready contract builder 只把 scene registry、DSL、UI base contract、provider payload 与 semantic bridge 合成为运行时场景契约，不得推导客户/供应商、个人/企业、合同或资金事实。

### 2026-05-06 P0-54 第五十二轮落地

已执行：

- `app_config_engine.controllers.contract_api` 补齐 contract HTTP controller source authority。
- `handler_registry` 补齐 intent handler registry source authority。
- legacy `view_Parser` 三组 mixin 文件补齐 view parser source authority：
  - `parsers Tree Form.py`
  - `parsers Kanban Pivot Graph.py`
  - `parsers_Calendar_Gantt Activity.py`
- `intent_acl_mode_guard` / `intent_write_guard` 补齐静态 guard source authority。
- 扩展 native alignment 边界测试，覆盖 contract controller、handler registry、带空格文件名 parser mixin 和静态 guard。

边界结论：

- contract HTTP controller 只接收 `/api/contract/get` 请求并委托 `ContractService`，可作为请求代理，但不解释业务事实。
- handler registry 只扫描并注册 intent handler 类，不能从 intent 名称、菜单或 handler 分发表推断客户/供应商。
- legacy view parser mixin 只解析 Odoo tree/form/kanban/pivot/graph/calendar/gantt/activity/search 视图结构。
- 静态 guard 只基于 Python AST 检查写意图权限声明，不读取模拟生产数据，也不承担任何业务事实权威。

### 2026-05-06 P0-55 第五十三轮落地

已执行：

- 对非测试、非空、非 `__init__` 的 `smart_core` Python 文件执行全口径 source authority 缺口扫描，结果已清零。
- `handlers.reason_codes` 补齐 handler 层 reason code metadata proxy source authority。
- `pre-migration.py` / `post-migration.py` 补齐 schema migration source authority。
- 六个 scene entry orchestrator 子类显式声明继承 `scene_entry_runtime_projection_adapter` 边界：
  - `CostTrackingContractOrchestrator`
  - `PaymentSliceContractOrchestrator`
  - `ProjectDashboardSceneOrchestrator`
  - `ProjectExecutionSceneOrchestrator`
  - `ProjectPlanBootstrapSceneOrchestrator`
  - `SettlementSliceContractOrchestrator`
- legacy `KanbanDynamicService` 补齐 runtime proxy source authority。
- legacy `KanbanViewParser` 补齐 kanban view parser projection source authority。
- 扩展 native alignment 边界测试，覆盖 handler reason code metadata proxy。

边界结论：

- reason code handler 只是 `utils.reason_codes` 的 metadata 代理，不得把 reason code 当作客户/供应商分类事实。
- migration 脚本只改 schema、索引和 UI 配置维度字段，不解释往来单位、合同或资金事实。
- scene entry orchestrator 子类只连接行业扩展服务并包装场景入口契约；业务事实权威留在被委托的行业服务。
- legacy kanban 动态服务可以代理 ORM 读写和 action 执行，但必须受权限服务约束，不能成为业务事实解释层。
- 全口径缺口扫描清零表示：除空文件、包初始化、manifest 与测试外，`smart_core` 可运行 Python 模块均已具备显式 source authority 边界声明。

### 2026-05-06 P0-56 第五十四轮落地

已执行：

- 对 `smart_core` 内客户/供应商/合同/付款/partner 等关键词做语义越界复查。
- `ApiDataHandler._source_authority_contract()` 补充 `no_business_fact_authority=True` 与 `field_value_passthrough_only=True`。
- `ApiDataWriteHandler._source_authority_contract()` 补充 `no_business_fact_authority=True` 与 `field_value_passthrough_only=True`。
- 调整 `ApiDataHandler` 子表创建注释，明确只是复制后端同名字段值以保留 ORM 事实，不分类 partner。
- `ui_base_contract_asset_producer.source_authority_contract()` 补充 `fallback_model_is_ui_placeholder=True`，明确 fallback `res.partner` 只是 UI 最小契约占位。
- `contract_governance.source_authority_contract()` 补充 `field_label_projection_only=True` 与 `no_partner_classification=True`。
- 扩展 native alignment 边界测试，覆盖 ORM 代理模型级 source、UI base fallback 和 governance partner 字段标签投影。

边界结论：

- `api_data` / `api_data_write` 可读写 Odoo ORM 字段值，但只是按模型、字段和 ACL 代理，不得将 `res.partner`、`partner_id` 或任意字段值解释为客户/供应商分类。
- 子表创建时复制 `company_id`、`currency_id`、`partner_id` 是为了避免前端推断隐藏必填字段；该动作只保留父记录事实，不产生新业务语义。
- UI base contract fallback 中的 `res.partner` 只是保证最小 UI 契约可构造的占位模型，不是客户/供应商事实来源。
- `contract_governance` 中的 `partner_id`、合同、付款等文本只用于列选择、字段标签、布局治理和 legacy 页面文案，不能作为业务事实分类依据。

### 2026-05-06 P1 内核冗余第一轮落地

已执行：

- 新增 `addons/smart_core/core/source_authority.py`，统一构造 `source_authority_contract` 的基础形状。
- 先收敛 8 个 semantic bridge 模块的重复 metadata 构造逻辑：
  - `page_contract_parser_semantic_bridge.py`
  - `page_contract_semantic_orchestration_bridge.py`
  - `runtime_page_parser_semantic_bridge.py`
  - `runtime_page_semantic_orchestration_bridge.py`
  - `scene_ready_parser_semantic_bridge.py`
  - `scene_ready_semantic_orchestration_bridge.py`
  - `scene_contract_parser_semantic_bridge.py`
  - `scene_contract_semantic_orchestration_bridge.py`
- 删除 4 个未被 `models/__init__.py` 加载、无模型定义、0 字节的占位文件：
  - `app.contract.cache.py`
  - `app.ui.config.py`
  - `app.rule.config.py`
  - `app.kpi.config.py`

下一轮建议：

- 扩展 `source_authority.py` 到 `system_init_*`、`unified_page_contract_*` 和 delivery 小服务。
- 继续拆分 “桥接模块重复 helper” 与 “业务切片 orchestration adapter” 两类冗余，避免一次性大迁移。

### 2026-05-06 P1 内核冗余第二轮落地

已执行：

- 继续复用 `addons/smart_core/core/source_authority.py`，收敛 Unified Page Contract 相关模块的重复 source authority 构造逻辑：
  - `unified_page_contract_lite_adapter.py`
  - `unified_page_contract_lite_patch_normalizer.py`
  - `unified_page_contract_lite_preview.py`
  - `unified_page_contract_lite_source_normalizer.py`
  - `unified_page_contract_v2_action.py`
  - `unified_page_contract_v2_assembler.py`
  - `unified_page_contract_v2_client.py`
  - `unified_page_contract_v2_data.py`
  - `unified_page_contract_v2_runtime.py`
  - `unified_page_contract_v2_status.py`
- 收敛两个函数式 system init 模块的重复 source authority 构造逻辑：
  - `system_init_dictionary_data_helper.py`
  - `system_init_scene_runtime_semantic_bridge.py`

边界结论：

- 本轮只统一 metadata 生成入口，不改变 source kind、authorities、runtime carrier 或契约输出结构。
- `unified_page_contract_*` 仍然只承担 v2/lite 契约投影、裁剪、patch normalization 和 runtime schema 投影，不承载业务事实权威。
- `system_init_dictionary_data_helper` 只投影 `sc.dictionary` 的启动字典数据。
- `system_init_scene_runtime_semantic_bridge` 只把 scene ready / semantic runtime surface 投影到 system init runtime surface。

下一轮建议：

- 对 class-based `system_init_*` builder/context/helper 做同样收敛，但保留各自的额外标志位。
- 将 `delivery/*` 中重复的 source authority 构造改为统一 helper，优先处理无额外 legacy contract 的小服务。

### 2026-05-06 P1 内核冗余第三轮落地

已执行：

- 继续复用 `addons/smart_core/core/source_authority.py`，收敛 class-based `system_init_*` builder/context/helper 的重复 source authority 构造逻辑：
  - `system_init_components_factory.py`
  - `system_init_diagnostics_helper.py`
  - `system_init_identity_payload.py`
  - `system_init_nav_request_builder.py`
  - `system_init_preload_builder.py`
  - `system_init_response_meta_builder.py`
  - `system_init_runtime_context.py`
  - `system_init_scene_runtime_surface_builder.py`
  - `system_init_scene_runtime_surface_context.py`
  - `system_init_surface_builder.py`
  - `system_init_surface_context.py`
- 收敛 `system_init_extension_fact_merger.py` 的重复 source authority 构造逻辑，并保留 `delegates_business_fact_authority=True`。
- 暂不改 `system_init_payload_builder.py`，因为其 source authority 现有输出没有 `rebuildable` 字段；后续若统一，应先确认是否允许补齐该字段。

边界结论：

- 本轮保留各模块原有额外标志位，如 `identity_surface_only`、`request_projection_only`、`startup_preload_only`、`response_envelope_only`、`startup_surface_only`、`scene_runtime_surface_only`。
- `system_init_*` 模块仍只承担启动 payload、runtime context、surface、diagnostics、preload 和 extension fact merger 的投影/载体职责。
- extension fact merger 只合并扩展贡献并显式声明业务事实权威被委托给 extension hook，不在 `smart_core` 内解释业务事实。

下一轮建议：

- 处理 `delivery/*` 中无复杂 legacy source contract 的小服务。
- 单独评估 `system_init_payload_builder.py` 是否补齐 `rebuildable=True`，避免在同一轮混入契约形状变化。

### 2026-05-06 P1 内核冗余第四轮落地

已执行：

- 继续复用 `addons/smart_core/core/source_authority.py`，收敛 delivery 层无复杂 legacy 子契约的小服务 source authority 构造逻辑：
  - `capability_service.py`
  - `delivery_engine.py`
  - `menu_fact_service.py`
  - `menu_service.py`
  - `release_audit_trail_service.py`
  - `release_operator_contract_registry.py`
  - `release_operator_contract_versions.py`
  - `release_operator_read_model_service.py`
  - `release_operator_surface_service.py`
  - `scene_snapshot_service.py`
- 保留各模块原有额外字段：
  - `fact_authority`
  - `contract_metadata_only`
  - `write_proxy`
  - `runtime_carrier`

边界结论：

- 本轮只统一 metadata 生成入口，不改变 delivery engine、menu projection、release operator surface、scene snapshot cache 的业务行为。
- `menu_fact_service` 仍只投影 Odoo 原生 `ir.ui.menu`、action、group 和 xmlid 事实。
- `scene_snapshot_service` 的 `write_proxy=True` 明确保留，表示它可写场景快照缓存，但不承担业务事实权威。
- `release_operator_*` 仍只承担发布操作台读模型、surface 和契约版本 registry 投影。

下一轮建议：

- 对 `product_identity.py`、`edition_release_snapshot_service.py`、`release_approval_policy_service.py`、`product_policy_service.py` 等带 legacy/default 子契约的模块单独整理。
- `scene_service.py` 当前 source authority 没有 `rebuildable` 字段，是否补齐需要单独确认契约形状。

### 2026-05-06 P1 内核冗余第五轮落地

已执行：

- 扩展 `addons/smart_core/core/source_authority.py`，允许 `rebuildable=None` 时省略该字段，用于保留 legacy/default 模块既有 source authority 输出形状。
- 收敛带 legacy/default 子契约或原先缺少 `rebuildable` 字段的 delivery 模块：
  - `product_identity.py`
  - `edition_release_snapshot_promotion_service.py`
  - `edition_release_snapshot_service.py`
  - `release_approval_policy_service.py`
  - `product_policy_service.py`
  - `scene_service.py`
- 保留各模块原有字段形状：
  - `fallback_base_product_key`
  - `legacy_default_base_source`
  - `legacy_default_role_source`
  - `legacy_role_resolver`
  - `fallback_policy_provider`
  - `legacy_policy_node_source`
  - `legacy_compatibility`
  - `legacy_default`
  - `write_proxy`

边界结论：

- `product_identity` 仍只解析 request/default product identity；legacy default base 只是兼容默认值，不是业务事实权威。
- `edition_release_snapshot_promotion_service` 是写代理，保留 `projection_only=False` 与 `write_proxy=True`。
- `edition_release_snapshot_service` 仍只投影发布快照和 delivery engine 输出；legacy role fallback 只用于兼容默认角色。
- `release_approval_policy_service` 仍只投影 release action policy / group / extension role resolver，不在 core 内定义业务角色事实。
- `product_policy_service` 的 default policy 和 policy node source 仍明确标记 legacy/default projection。
- `scene_service` 继续只把 policy、scene snapshot 和 scene contract 投影成 delivery scene entries；本轮未补 `rebuildable` 字段，避免改变契约形状。

下一轮建议：

- 重新扫描剩余未接入 `build_source_authority_contract` 的非测试 Python 模块，按“输出形状不变”原则分批收敛。
- 对 `system_init_payload_builder.py` 是否补 `rebuildable=True` 单独做兼容性判断。

### 2026-05-06 P1 内核冗余第六轮落地

已执行：

- 继续复用 `addons/smart_core/core/source_authority.py`，收敛 core 基础小模块的 source authority 构造逻辑：
  - `action_target_schema.py`
  - `extension_loader.py`
  - `command_registry.py`
  - `trace.py`
  - `hash_utils.py`
  - `exceptions.py`
  - `scene_registry_provider.py`
  - `orchestration_semantics.py`
  - `ui_base_contract_asset_event_queue.py`
  - `delivery_capability_entry_defaults.py`
  - `delivery_menu_defaults.py`
- 保留各模块原有额外字段：
  - `legacy_compatibility`
  - `write_proxy`
  - `capability_entry_default_only`
  - `synthetic_navigation_only`
  - `runtime_carrier`
- `scene_registry_provider.py` 原本无 `rebuildable` 字段，本轮继续通过 `rebuildable=None` 保持输出形状。

边界结论：

- 本轮模块均为 core 基础工具、静态 schema、兼容 registry、trace/hash/error envelope、scene registry 投影或 delivery 默认节点构造，不承担业务事实权威。
- `ui_base_contract_asset_event_queue` 保留 `write_proxy=True`，表示它只写 UI base contract asset 刷新队列。
- `delivery_menu_defaults` 与 `delivery_capability_entry_defaults` 只生成 synthetic/default UI 节点，不作为菜单、能力或业务模型事实来源。

下一轮建议：

- 继续收敛 builder/provider 类模块，如 `page_contracts_builder.py`、`runtime_page_contract_builder.py`、`scene_contract_builder.py`、`scene_ready_contract_builder.py`。
- 对含 legacy copy source 的 builder 保留对应 legacy source 字段，不改变契约输出形状。

### 2026-05-06 P1 内核冗余第七轮落地

已执行：

- 继续复用 `addons/smart_core/core/source_authority.py`，收敛主要 contract builder / provider 模块的 source authority 构造逻辑：
  - `page_contracts_builder.py`
  - `runtime_page_contract_builder.py`
  - `scene_contract_builder.py`
  - `scene_ready_contract_builder.py`
  - `workspace_home_contract_builder.py`
  - `workspace_home_data_provider.py`
- 保留 legacy/source 额外字段：
  - `legacy_page_copy_source`
  - `legacy_product_title_source`
  - `scene_runtime_contract_only`
  - `legacy_workspace_keyword_policy`
  - `delegated_source_authority`
  - `adapter_layer`
  - `provider_module`
- `workspace_home_contract_builder.py` 和 `workspace_home_data_provider.py` 原本无 `rebuildable` 字段，本轮继续通过 `rebuildable=None` 保持输出形状。

边界结论：

- page/runtime/scene/scene-ready builder 仍只做契约投影和 runtime surface 装配，不承担业务事实权威。
- legacy page copy、legacy product title 和 workspace keyword policy 仍明确标记为 legacy projection。
- workspace home provider 仍是行业内容 provider adapter，实际行业事实权威只能来自 delegated provider，不在 `smart_core` 内部定义。

下一轮建议：

- 继续处理 `scene_provider.py`、`scene_runtime_orchestrator.py`、`scene_delivery_policy.py`、`release_navigation_contract_builder.py` 等场景交付链路。
- 对带多个 legacy/default source contract 的模块继续保持“小步替换 + 输出形状检查”。

### 2026-05-06 P1 内核冗余第八轮落地

已执行：

- 继续复用 `addons/smart_core/core/source_authority.py`，收敛场景交付链路 source authority 构造逻辑：
  - `scene_provider.py`
  - `scene_runtime_orchestrator.py`
  - `scene_delivery_policy.py`
  - `release_navigation_contract_builder.py`
  - `scene_nav_contract_builder.py`
  - `scene_channel_policy.py`
  - `scene_merge_resolver.py`
  - `scene_governance_payload_builder.py`
  - `scene_diagnostics_builder.py`
  - `scene_dsl_compiler.py`
- 保留 legacy / delegated 字段：
  - `delegated_source_authority`
  - `legacy_surface_aliases`
  - `legacy_surface_alias_source`
  - `legacy_fallback`
  - `legacy_compatibility`
  - `runtime_carrier`
- `release_navigation_contract_builder.py` 原本无 `rebuildable` 字段，本轮继续通过 `rebuildable=None` 保持输出形状。

边界结论：

- 场景 provider、runtime orchestrator、delivery policy、nav contract、merge resolver、diagnostics 和 DSL compiler 均只承担场景契约投影、运行时编排或治理 payload 组装。
- legacy surface alias 与 release navigation fallback 仍明确标记为 legacy projection。
- scene provider 的 delegated scene registry source 保留嵌套，不把 `sc.scene` / `sc.capability` / menu/action/group 事实权威混入 provider 自身。

下一轮建议：

- 收敛 intent/runtime 基础模块：`base_handler.py`、`intent_router.py`、`intent_execution_result.py`、`context.py`、`middlewares.py`、`handler_registry.py`。
- 继续保持 write proxy、runtime registry、request context 等额外字段不变。
