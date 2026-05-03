# Odoo 原生能力对齐盘点 v1

分支：`codex/odoo-native-capability-alignment`

目标：盘点当前产品事实层、场景页、统一前端契约与 Odoo 原生能力之间的重叠区，判断哪些需求可以直接复用 Odoo，哪些需要保留自定义契约适配层，哪些应避免继续自建。

## 结论摘要

当前系统已经正确复用了 Odoo 的 ORM、权限、菜单、动作、视图、消息、活动、附件、分组聚合和多公司上下文等基础能力。主要偏离不在业务模型本身，而在“统一前端为了脱离 Odoo WebClient 后重新实现的一批通用体验”：列表搜索、收藏筛选、列偏好、通用 CRUD、附件下载上传、chatter 展示、审批/工作流、仪表盘聚合、高级视图降级。

建议下一轮按“原生优先、契约投影、前端只渲染”的原则收口：

- 业务事实模型继续保留：工程施工行业对象、历史承接模型、投影汇总模型是产品差异化资产。
- Odoo 原生元数据成为事实来源：模型字段、视图结构、菜单动作、权限、搜索视图、`ir.filters`、`mail.activity`、`mail.message`、`ir.attachment` 不应再复制一套事实。
- 自定义契约层只做投影和治理：`smart_core` 可以继续把 Odoo 原生能力投影成 SPA 能消费的契约，但不要把偏好、搜索、审批、附件、消息等变成另一套事实主数据。

## 已经对齐良好的原生能力

### 模型与 ORM

证据：

- 大量业务对象直接使用 Odoo `models.Model`、`fields.*`、`@api.depends`、`create/write/unlink`。
- 关键业务域继承或扩展原生模型，如 `project.project`、`project.task`、`purchase.order`、`account.move`、`product.product`、`stock.*`。
- 统计计算大量使用 `read_group`，例如项目、付款、合同、附件计数等。

判断：

这部分方向正确。行业事实应该以 Odoo 模型为主，不需要迁移到外部自定义存储。

### 权限、菜单、动作、视图

证据：

- 使用 `ir.model.access.csv`、record rules、`res.groups`。
- 菜单和动作通过 XML 定义，动作类型是 `ir.actions.act_window`。
- `smart_core` 已经有 `native_view_contract_projection.py`、view parser、`load_view`、`contract_governance` 等投影能力。

判断：

Odoo 原生的菜单、动作、视图、权限应继续作为系统事实来源。前端契约可以消费它们，但不应重新维护一套独立的菜单/权限事实。

### 消息、活动、附件

证据：

- 大量业务模型继承 `mail.thread`、`mail.activity.mixin`。
- 业务动作中使用 `message_post`、`activity_schedule`。
- 附件以 `ir.attachment` 承载，部分业务模型有附件 Many2many。

判断：

这些是 Odoo 很成熟的原生能力。我们的前端需要的是统一展示与权限裁剪，不是替代它们。

## 需要优先对齐的能力

### 1. 搜索、分组、收藏筛选

现状：

- `app.search.config` 会解析 search view、`ir.filters` 并生成搜索契约。
- 前端有自定义搜索分组控件、保存收藏筛选能力。
- `search.favorite.set` 最终写入 `ir.filters`。

原生能力：

- Odoo search view 定义过滤器、分组候选、上下文。
- `ir.filters` 原生支持个人/共享/默认筛选。
- ORM `search/read_group` 支持 domain、context、group_by、排序。

差距：

- 我们已经把收藏写回 `ir.filters`，方向正确。
- 风险在于 `app.search.config.search_def` 容易成为第二份搜索事实，尤其默认 limit、group_by 候选、默认筛选等如果长期缓存不刷新，会和 search view / `ir.filters` 漂移。

建议：

- 搜索事实来源固定为 search view + `ir.filters`。
- `app.search.config` 定位为“可重建缓存/投影”，不得作为人工维护事实。
- 升级流程必须包含搜索契约重建或缓存失效。
- 前端保存收藏只写 `ir.filters`，不要另建收藏模型。

### 2. 用户列表列偏好

现状：

- 自定义模型 `sc.user.view.preference` 存储 `list_columns` 等用户偏好。

原生能力：

- Odoo 原生 WebClient 有用户视图状态、收藏、搜索默认值等机制，但列显隐偏好在原生模型层并不是稳定业务事实。

判断：

这块可以保留自定义，但要降级为“前端表现偏好”，不能参与业务事实、权限或交付契约治理。

建议：

- `sc.user.view.preference` 保留，但明确为 UI preference。
- scope 必须绑定 `action_id + model + view_type + user`，避免不同场景相互污染。
- 不要把列偏好写入场景包、菜单事实或业务模型。

### 3. 通用数据接口 `api.data`

现状：

- 前端通过 `api.data` 做 list/read/count/export/batch。
- 后端仍调用 Odoo ORM、`read_group`、权限检查、record rule。

原生能力：

- Odoo RPC/WebClient 本身已支持 `search_read`、`read_group`、`onchange`、`write/create/unlink`。

判断：

因为我们有独立 SPA 和统一 intent 协议，`api.data` 可以保留。但它必须是“安全代理”，不是新数据层。

建议：

- 继续复用 ORM 权限、record rule、字段权限、company context。
- 避免在 `api.data` 中引入与业务模型重复的状态机或字段解释。
- 对 list/read/write/export 的行为做原生语义对齐测试：domain、context、active_test、多公司、record rule、read_group 聚合。

### 4. 表单 onchange 与按钮执行

现状：

- `api_onchange`、`execute_button`、`app.action.gateway` 用 intent 包装 Odoo 方法。

原生能力：

- Odoo `onchange`、button object/action、server action、window action。

判断：

保留 intent 包装是合理的，但前端不应自造表单业务逻辑。按钮可见性、只读、必填、domain、onchange 结果应来自原生 view/modifier/onchange。

建议：

- 把 view parser 对 modifiers、domain、context、onchange 字段的提取列为 P0 对齐项。
- 自定义前端只消费契约 patch，不自行推断业务规则。

### 5. Chatter、待办、我的工作

现状：

- 前端有 `chatter.timeline`、`chatter.post`、`chatter.activity.schedule`。
- “我的工作”聚合了 `mail.activity`、关注、消息、业务工作项。

原生能力：

- `mail.message` 承载消息时间线。
- `mail.activity` 承载待办活动。
- `mail.thread` 的 follower/subtype 机制承载关注与通知。

差距：

- “我的工作”可以聚合，但不要把失败重试、关注消息、项目名称等作为独立工作事实。
- 用户能做什么应由 `mail.activity` 和对应业务记录动作共同决定。

建议：

- 我的工作主线优先使用 `mail.activity`。
- 关注/消息只作为“动态/提醒”，不要混成待办处理。
- 工作项点击必须落到真实 Odoo action/record，不落到只显示名称的壳。

### 6. 附件上传下载

现状：

- `file.upload`、`file.download` 包装 `ir.attachment`。
- 上传有 allowlist 和大小限制。

原生能力：

- `ir.attachment`、`/web/content`、访问规则、chatter 附件。

判断：

保留包装接口可以，但应尽量对齐 `/web/content` 语义，避免 base64 大文件绕路和重复权限逻辑。

建议：

- 下载优先返回 Odoo content URL 或流式响应，不长期走 base64 payload。
- 上传统一落 `ir.attachment`，并复用 record rule 与 `check_access_rule`。
- 附件列表直接来自 `ir.attachment` 或 chatter，不维护业务侧重复附件事实，除非业务确实需要附件分类/必备资料规则。

### 7. 审批与工作流

现状：

- 已依赖 `base_tier_validation`。
- 同时存在 `sc.approval.policy`、`sc.approval.step` 和 `sc.workflow.*` 自建工作流模型。
- 多个业务模型继承 `tier.validation`，但部分逻辑仍使用自定义状态按钮和 policy 判断。

原生/现有可复用能力：

- `base_tier_validation` 已经提供分级审批的核心机制。
- Odoo server action、mail activity、groups 可以承接审批动作、提醒和权限。

风险：

- `sc.workflow.*` 容易和 `base_tier_validation` 形成两套审批事实。
- `sc.approval.policy` 如果只是配置同步层，可以保留；如果运行时自己驱动审批实例，则会偏离。

建议：

- 审批运行时以 `base_tier_validation` 为准。
- `sc.approval.policy` 定位为业务友好的配置入口和同步器。
- `sc.workflow.*` 暂停扩大使用，评估是否降级为历史兼容或迁移到 tier validation。

### 8. 看板、透视、图表、日历、甘特、活动视图

现状：

- 前端对 pivot/graph/calendar/gantt/activity 有“可读降级视图”。
- kanban 有自定义渲染。

原生能力：

- Odoo 原生 view types 已支持 tree/form/kanban/pivot/graph/calendar/activity，部分企业版支持 gantt。

差距：

- 我们现在把高级视图降级为列表/卡片，会损失原生语义。
- 但独立 SPA 不直接运行 Odoo WebClient，因此需要契约投影。

建议：

- tree/form/kanban 优先做完整契约投影。
- pivot/graph 优先复用 `read_group` 和原生 view arch 的 measure/group 配置。
- calendar/activity 直接解析原生 view arch 的日期字段、状态字段和活动模型。
- gantt 如无企业模块能力，不承诺原生对齐，只保留降级。

### 9. 仪表盘与报表

现状：

- 有 `dashboard.company`、项目驾驶舱、投影汇总模型、`project_dashboard_service`。
- `smart_core` 还有 dashboard/dashboard_widget 模型。

原生能力：

- `read_group`、SQL view/model、Odoo graph/pivot、spreadsheet/dashboard 生态。

判断：

行业驾驶舱是产品差异化，可以保留自定义场景页。但数据事实应来自业务模型、投影模型或 SQL view，不应由前端造数。

建议：

- 公司驾驶舱只消费真实模型/投影汇总。
- 对可下钻指标，必须绑定 Odoo action/domain。
- 对纯图表型需求，优先用 graph/pivot 的语义配置生成契约，不新增重复 dashboard widget 事实。

### 10. 场景编排、交付治理、菜单治理

现状：

- `smart_construction_scene`、`smart_scene`、`scene_registry`、scene package/channel/governance/log 等自建能力较多。
- 近期明确了业务事实层只能有模型、视图、权限、菜单。

原生能力：

- Odoo 模块安装升级、XML data、`ir.module.module`、菜单/action/view/security 原生就是交付事实。

判断：

场景包和治理可以作为产品交付层保留，但不能混入业务事实层。业务事实层仍应回到 Odoo 原生四类：模型、视图、权限、菜单。

建议：

- 场景编排层只引用原生 action/menu/view/model，不复制字段和权限事实。
- 发布、回滚、渠道是交付治理，不进入业务事实模块。
- 新建业务模块时禁止新增 scene-only 的业务字段或前端专用事实模型。

## 原生能力对齐优先级

P0：下一轮必须约束

- 搜索事实：search view + `ir.filters` 为准，`app.search.config` 可重建。
- 权限事实：ACL/record rule/groups 为准，前端不自判业务权限。
- 我的工作：`mail.activity` 是待办主事实，消息/关注只作为动态。
- 附件：`ir.attachment` 为准，上传下载包装不能复制附件事实。
- 审批：`base_tier_validation` 是审批运行时主事实，自建 workflow 暂停扩张。

P1：逐步增强

- form modifiers/onchange/button 投影完整性。
- pivot/graph/calendar/activity 原生 view arch 投影。
- 用户列偏好边界收窄为 UI preference。
- 驾驶舱指标全部绑定真实模型和可下钻 action/domain。

P2：长期治理

- 评估 `sc.workflow.*` 的迁移/废弃路径。
- 评估 dashboard/dashboard_widget 与场景页指标配置是否重复。
- 清理旧 portal shell 与新 SPA 场景页之间的重复入口。

## 建议验收标准

每个“可复用 Odoo 原生能力”的需求都应回答四个问题：

1. 原生事实在哪里：model/view/action/menu/group/rule/filter/message/activity/attachment？
2. 自定义层是否只是投影：是否可删除并从原生事实重建？
3. 用户历史数据是否能承接：旧库升级后是否无需手工补投影？
4. 前端是否只渲染真实数据：无数据时显示空状态，不造概念数据。

## 下一步建议

1. 先做 P0 对齐审计测试：搜索收藏、我的工作、附件、审批、权限。
2. 给 `app.search.config`、`sc.user.view.preference`、`sc.approval.policy`、`sc.workflow.*` 加边界说明或迁移计划。
3. 选一个典型模型，例如 `payment.request` 或 `project.project`，验证从 Odoo 原生 action/view/search/filter/activity/attachment 到 SPA 契约的完整链路。

## 本分支执行记录

已落地的 P0 边界：

- `app.search.config` 明确为 `odoo_native_search_projection`，来源权威是 search view、`ir.filters` 和字段元数据，契约可重建。
- `sc.user.view.preference` 明确为 UI-only 偏好，新 scope 使用 `ui:` 前缀；读取时兼容旧 scope，避免旧库用户列设置失效。
- `sc.approval.policy` 明确审批运行时权威是 `base_tier_validation`，本模型只做业务配置入口和同步器。
- `sc.workflow.*` 标记为 legacy workflow，默认禁止发布和创建新运行时实例；只有显式设置 `sc.workflow.legacy_runtime_enabled` 或上下文 `allow_legacy_workflow_runtime` 才允许兼容运行。
- 新增边界回归测试，覆盖搜索投影来源、UI-only 偏好 scope、审批运行时权威和 legacy workflow 默认关闭。
- `my.work.summary` 明确 `mail.activity` 是待办主事实；`mail.message`、`mail.followers` 只作为协作/关注信号，`sc.workflow.workitem` 只作为 legacy todo authority。
- `chatter.*` 和 `file.*` intent 明确原生事实源：`mail.message`、`mail.activity`、`ir.attachment`。
- `api.data`、`api.data.write`、`api.data.unlink`、`api.data.batch` 明确为 Odoo ORM 安全代理，权威来源是 ORM、ACL、record rule 和字段元数据，不形成新数据层。
- `api.onchange` 明确为 Odoo onchange 代理；`execute_button` 明确为 Odoo 模型按钮/动作代理，前端不自行承载表单业务规则或按钮业务运行时。
- `load_contract` 明确为 Odoo 原生契约投影，权威来源是 `ir.ui.view`、`ir.actions.act_window`、`ir.ui.menu`、字段、ACL 和 record rule；`load_view` 仅作为兼容代理，不再形成第二条视图解析主链路。
- 公司驾驶舱、项目驾驶舱和项目驾驶舱 block 明确为业务事实投影，指标来源必须是 Odoo ORM、`read_group`、业务模型、投影模型或证据服务，前端不得合成业务指标。
- `app.report.config` 明确为 `ir.actions.report` 的可重建报表契约投影，按 `res.groups` 做运行态过滤，不形成第二套报表事实。
- `sc.scene`、`sc.capability`、场景包和场景治理 handler 明确为交付编排/治理层，只引用 `ir.ui.menu`、`ir.actions`、`res.groups` 和 intent，不作为业务事实权威。
- `app.model/action/menu/permission/view/validator.config` 明确为 Odoo 原生元数据可重建投影，`app.view.fragment/variant` 明确为 UI overlay，`sc.ui.base.contract.asset` 明确为可重建契约缓存。
- `app.workflow.config` 明确为状态字段、表单按钮和 `mail.activity.type` 的可重建投影；运行时权威仍是 Odoo 模型方法和 `mail.activity`，不是第二套工作流运行时。
- 付款、成本、结算、项目执行、计划准备等自定义场景切片明确为 `scene_entry_and_block_contract` 业务事实投影；entry 和 runtime block 都必须暴露 `source_authority`，事实来源仍是 `project.project`、`project.task`、付款/成本/合同等业务模型与 Odoo ORM/read_group。
- `workspace.home` 明确为角色首页的 Odoo 原生能力聚合投影，只引用项目、付款、风险、菜单/action/group 等事实，不作为业务事实权威。
- `project.initiation.enter` 明确为 Odoo ORM 写入代理，写入权威是 `project.project.create`，初始化任务和消息只通过 `project.task`、`mail.message` 等原生模型完成。
- 运行时写操作继续收口：付款/成本记录创建分别声明为 `payment.request.create`、`account.move.create` 的 Odoo ORM 写代理；付款审批/执行声明为 `payment.request` 模型方法和 tier review 运行时代理；项目执行推进声明为项目/任务模型状态推进代理；风险动作声明为 `project.risk.action` 模型方法代理；我的工作完成待办声明为 `mail.activity.action_feedback` 代理。
- 应用目录、应用导航、应用打开、能力说明/可见性报告明确为交付层投影，只引用 `ir.ui.menu`、`ir.actions`、`res.groups`、`sc.capability` 等交付事实，不作为业务事实权威。
- 证据链追踪、项目上下文选择/解析、项目驾驶舱兼容打开入口补充 source authority；usage/telemetry/system ping 明确为观测数据或健康检查，不进入业务事实层。
- `system.init`、`ui.contract`、权限检查、元数据描述、意图目录、搜索收藏、登录/session bootstrap、用户视图偏好、场景健康/场景包安装清单补充来源边界：它们分别是启动面、UI 契约、权限、元数据、交付目录、筛选器写代理、认证会话代理、UI-only 偏好或治理投影，不作为业务事实权威。
- `app.action.gateway`、契约 sanitizer、`ui_base_contract_asset` 事件触发器补充来源边界：只代理 Odoo 模型方法/onchange、清洗契约 payload 或触发可重建契约缓存失效，不沉淀业务事实。
- `sample.enhanced`、`ui.contract.enhanced`、`ui.contract.model.view` 作为 legacy enhanced/sample 入口已删除；契约用例、导出快照、readiness policy、intent surface coverage gate 和生产链路 guard 同步清理，避免被重新纳入正式能力面。
- `enhanced_intent_dispatcher`、`enhanced_intent_router` 旧实验链路已删除；生产链路只保留 `/api/v1/intent`、`intent_dispatcher`、`intent_router`，纯度 guard 和生产链路 guard 同步收口。
