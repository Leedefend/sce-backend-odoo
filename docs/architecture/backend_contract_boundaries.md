# 后端契约职责边界

## 目标

后端契约层必须先回答“谁是事实权威、谁只是投影、谁可以覆盖谁”，再允许写代码或写数据。低代码配置、行业标准版、特定用户偏好、平台内核不能混用同一套隐含规则。

产品边界必须先于实现边界判断。正式产品归属见 `docs/product/formal_product_boundary_v1.md`；本文件只定义落到后端契约和运行时写入后的技术规则。

## 正式产品归属

| 正式产品 | 当前载体 | 后端契约职责 |
| --- | --- | --- |
| 平台内核产品 | `smart_core` | 提供契约、配置、版本、发布、回滚、审计和通用装配机制 |
| 施工行业标准产品 | `smart_construction_core` | 发布施工行业默认模型、菜单、表单、列表、搜索、审批和业务分类 |
| 特定用户产品 | `smart_construction_custom` 或独立客户模块 | 发布客户确认的菜单、表单、字段、角色、初始化数据和用户偏好投影 |
| 低代码配置产品 | 配置工作台和运行时配置表 | 保存管理员显式配置，并通过版本、审计、回滚覆盖默认配置 |
| 运维交付工具 | `scripts`、迁移、runbook | 迁移、修复、重放和验证；不能成为长期事实权威 |

## 分层

| 层级 | 载体 | 职责 | 禁止事项 |
| --- | --- | --- | --- |
| L0 平台内核 | `addons/smart_core/core`、intent envelope、认证、路由、基础契约协议 | 提供稳定协议、调度、权限与基础投影能力 | 写行业业务规则、写特定用户偏好、承载客户字段顺序 |
| L1 契约基础设施 | `ui.business.config.contract`、`ui.form.field.policy`、`ui.menu.config.policy`、contract assembler | 保存和合并配置，声明 source authority 与覆盖顺序 | 通过前端兜底猜测业务语义；用文件名后缀临时决定权威 |
| L2 行业标准版 | `smart_construction_core` 数据、模型、菜单、行业默认表单/列表/审批 | 发布行业通用默认配置和业务对象 | 承载单一客户偏好；覆盖用户运行时配置 |
| L3 用户模块 | `smart_construction_custom` 用户偏好、客户定制菜单、默认三栏风格 | 承载特定用户/企业的默认体验和上线初始化 | 直接修改平台内核；伪装成低代码用户即时配置 |
| L4 低代码运行时配置 | 配置工作台保存的表单、列表、菜单、审批配置 | 承载用户管理员在界面上的显式调整 | 修改业务事实；绕过版本、审计和作用域 |

## 运行时覆盖顺序

`ui.business.config.contract` 允许多个契约共同作用，但必须按后端统一分类排序：

1. `generated_industry_baseline`：生成的兜底行业基线。
2. `industry_standard_configuration`：行业标准版正式配置。
3. `user_preference_projection`：用户模块发布的偏好投影，例如三栏、不分 tab、菜单拆分。
4. `tenant_lowcode_configuration`：用户管理员通过低代码界面保存的显式配置。

同一层内再按作用域精度排序：全局配置先于 action/view/role 专项配置；专项配置最后生效。然后才比较 `priority/version/id`。

## 写入规则

- 低代码表单字段顺序、显隐、分组必须写入正式 view orchestration，并带 `view_orchestration.context.source = smart_core.lowcode.*`。
- 低代码菜单可见性、排序、父级调整必须写入 menu orchestration，并带 `menu_orchestration.source = smart_core.lowcode.menu_config`。
- 低代码审批启用、审批方式、审批步骤编排属于行业审批运行时策略，写入 `sc.approval.policy` / `sc.approval.step`，不写入表单或菜单契约；`source_authority` 必须声明 `lowcode_boundary = approval_policy`、`policy_source = sc.approval.policy`。
- 低代码“新增菜单”只创建运行时菜单入口和菜单配置策略，满足管理员即时调整；长期交付菜单必须沉淀到 L2 行业模块或 L3 用户模块。
- 低代码写入意图的 `source_authority` 必须声明 `lowcode_boundary` 和 `contract_source`，让审计能从响应元信息直接识别边界。
- 用户模块表单偏好必须写入 `view_orchestration.context.source = smart_construction_custom.*_form_preference`；即便契约名称是 `view_orchestration:*`，分类器也必须把它归入 L3 用户偏好投影。
- 用户模块可以写入偏好投影，但必须带 `smart_construction_custom.*preference` source，不能冒充低代码配置。
- 行业标准数据只能给默认结构和默认策略，不能处理特定用户看面。
- 运行时页面装配器不得给配置对象自身注入通用表单设计入口；审批、菜单、字段策略等对象使用专用配置面板。
- 通用 `api.data.write` / `api.data.create` 写代理不得写运行时配置模型；`ui.business.config.contract`、`ui.form.field.policy`、`ui.menu.config.policy`、`sc.approval.policy`、`sc.approval.step` 等必须走专用配置入口。
- 前端只消费后端契约和专用配置意图，不承担“判断哪一层覆盖哪一层”的职责。

## 迭代动手前检查

每次涉及表单、列表、菜单、审批、用户偏好、契约保存时，必须先回答：

1. 这次改动属于哪一个正式产品：平台产品、行业标准产品、用户产品、低代码配置产品，还是运维交付工具？
2. 这次改动属于 L0/L1/L2/L3/L4 哪一层？
3. 写入的权威表是什么？是否只是投影？
4. 是否会覆盖用户管理员已经通过低代码保存的配置？
5. 是否需要 source authority 或 `view_orchestration.context.source`？
6. 是否有运行时配置对象误进入通用表单设计器？
7. 是否需要浏览器验证配置端和业务端两条链路？

没有回答边界，不进入实现。

产品边界判断规则：

- 通用机制进入 `smart_core`；不得带施工行业或客户语义。
- 施工行业默认进入 `smart_construction_core`；不得承载单一客户偏好。
- 客户确认且需要重放的体验进入 `smart_construction_custom` 或客户模块；不得冒充低代码即时配置。
- 管理员在界面保存的即时调整进入低代码运行时配置；若确认长期生效，必须再沉淀到用户模块或行业模块。
- 一次性修复、迁移和验收进入脚本或 runbook；不得作为长期事实来源。

## 当前后端防线

- `smart_core.utils.backend_contract_boundaries` 统一维护运行时配置模型、契约分类和覆盖排序。
- `ui.business.config.contract._effective_view_orchestration_contracts()` 只使用统一排序函数决定生效顺序。
- 低代码字段配置和契约保存入口自动补齐 `view_orchestration.context.source`。
- `PageAssembler` 通过统一边界函数屏蔽配置运行时模型的通用表单设置入口。
- `scripts/verify/backend_contract_boundary_guard.py` 扫描后端直接写 `ui.business.config.contract`、低代码运行时策略表与审批运行时策略的入口；新增写入点必须先进入白名单并说明边界。
- 如需沉淀审计结果，可设置 `BACKEND_CONTRACT_BOUNDARY_GUARD_REPORT=...`，守卫会把同一份 JSON 报告写入指定文件。
- 守卫报告必须带 `schema_version`；当前版本为 `1.0`。
- 守卫报告中的 `writer_boundary_count` 表示写入边界角色数；`writer_file_count` 表示唯一文件数。同一 handler 同时写契约镜像和运行时策略时，会计入多个边界角色。
- 守卫报告中的每条 writer 必须带 `category`：`business_config_contract`、`lowcoding_policy_runtime` 或 `approval_policy_runtime`。
- 新增扫描类别必须新增 `BOUNDARY_RULES` 规则项，不能在 `build_report()` 中复制独立扫描分支。
- 表单配置写入意图的 `source_authority` 必须带 `lowcode_boundary = form_config` 和 `contract_source = smart_core.lowcode.form_field_policy`。
- 菜单配置写入意图的 `source_authority` 必须带 `lowcode_boundary = menu_config` 和 `contract_source = smart_core.lowcode.menu_config`。
- 审批配置写入意图的 `source_authority` 必须带 `lowcode_boundary = approval_policy` 和 `policy_source = sc.approval.policy`。
- 用户模块偏好 source 优先于契约名称分类，防止 `view_orchestration:*` 用户偏好被误判为 L4 低代码配置。

## 当前允许直接写契约表的入口

| 文件 | 层级 | 边界 | 预期 source |
| --- | --- | --- | --- |
| `addons/smart_core/model/ui_business_config_contract.py` | L1 | 契约基础设施自身：`contract_infrastructure` | n/a |
| `addons/smart_core/handlers/form_field_configuration.py` | L4 | 表单低代码运行时配置：`form_lowcode_runtime_config` | `smart_core.lowcode.form_field_policy` |
| `addons/smart_core/handlers/menu_configuration.py` | L4 | 菜单低代码运行时配置：`menu_lowcode_runtime_config` | `smart_core.lowcode.menu_config` |
| `addons/smart_construction_custom/models/user_preferences.py` | L3 | 用户偏好投影初始化：`user_preference_projection` | `smart_construction_custom.*preference` |
| `addons/smart_construction_core/models/support/formal_list_contract_sync.py` | L2 | 行业正式列表契约投影：`industry_formal_list_contract_projection` | `smart_construction_core.formal_settlement_list_contract_sync` |

## 当前允许直接写审批运行时策略的入口

| 文件 | 层级 | 边界 | 预期 source |
| --- | --- | --- | --- |
| `addons/smart_construction_core/handlers/approval_policy_configuration.py` | L2/L4 | 行业审批策略低代码配置：`approval_policy_runtime_configuration` | `smart_core.lowcode.approval_policy` |

## 当前允许直接写低代码运行时策略的入口

| 文件 | 层级 | 边界 | 预期 source |
| --- | --- | --- | --- |
| `addons/smart_core/handlers/form_field_configuration.py` | L4 | 表单字段低代码策略配置：`form_field_policy_runtime_configuration` | `smart_core.lowcode.form_field_policy` |
| `addons/smart_core/model/ui_form_custom_field_wizard.py` | L4 | 自定义字段同步表单策略：`form_custom_field_policy_creation` | `smart_core.lowcode.form_field_policy` |
| `addons/smart_core/handlers/menu_configuration.py` | L4 | 菜单低代码策略配置：`menu_config_policy_runtime_configuration` | `smart_core.lowcode.menu_config` |
| `addons/smart_construction_core/models/support/product_policy_sync.py` | L2 | 行业产品菜单默认策略投影：`industry_product_menu_policy_projection` | `smart_construction_core.product_policy_sync` |

新增直接写 `ui.business.config.contract` 的入口必须先更新本表和 `scripts/verify/backend_contract_boundary_guard.py`，并说明为什么不能通过现有 handler 或用户模块承载。
新增直接写 `sc.approval.policy` / `sc.approval.step` 的入口必须先更新本表和 `scripts/verify/backend_contract_boundary_guard.py`，并说明为什么不能通过审批配置 handler 承载。
新增直接写 `ui.form.field.policy` / `ui.menu.config.policy` 的入口必须先更新本表和 `scripts/verify/backend_contract_boundary_guard.py`，并说明为什么不能通过现有表单/菜单配置 handler 承载。
L2 行业默认策略入口只能发布默认看面，不能覆盖 L4 用户管理员在低代码界面保存的运行时配置。
