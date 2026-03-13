# 系统场景编排层完整设计与约束说明 v1

## 1. 文档目的

本文档用于明确系统中“场景编排层（Scene Orchestration Layer）”的定位、分层、能力边界、模块归属、输入输出契约、运行流程、治理要求与实施约束，作为系统后续开发、重构、扩展与验证的统一依据。

本文档适用于当前系统整体链路：

`Odoo 原生页面结构 → 原生结构解析层 → 场景编排层 → 前端渲染层`

本文档的目标不是复刻 Odoo 原生 Web Client，而是建立一套以原生页面结构为输入、以场景契约为输出的后端编排体系，使前端能够基于统一契约完成通用渲染与产品化交付。

## 2. 核心结论

### 2.1 场景编排层的本质定位

场景编排层是系统中的：

`用户场景解释器 + 页面语义组装器 + 契约输出引擎`

它负责将后端已解析的原生页面结构，结合当前用户场景、角色上下文、页面目标、权限结论与增强能力，组装为前端唯一消费的 `Scene Contract`。

### 2.2 场景编排层不是以下任意一种

场景编排层不是：

- 业务模型层
- 权限判定层
- 原始视图解析层
- 前端组件层
- 像素级 UI 设计层
- 单个业务页面模板仓库

它是一个平台中间能力层。

### 2.3 模块归属的最终结论

场景编排层必须采用：

`平台引擎 + 行业内容`

即：

#### 平台侧负责

- 编排引擎
- 标准契约
- zone/block/action 标准
- 注册机制
- 扩展点
- 治理与验证

#### 行业侧负责

- 具体 scene profile
- 行业页面优先级策略
- 行业 block 语义映射
- 行业增强能力装配策略
- 行业 action promotion 规则

## 3. 总体架构定位

建议在整体系统中，将场景编排层定位为独立的中间层，而不是揉进底层内核或散落在行业模块中。

### 3.1 推荐的三层组织方式

#### 3.1.1 `smart_core`

定位：平台基础内核。

负责：

- intent / contract 基础能力
- 通用 registry 基础设施
- 权限 verdict 基础结构
- schema / shape guard 公共能力
- 通用上下文与基础工具

#### 3.1.2 `smart_scene`（推荐新增或强化）

定位：平台级场景编排引擎模块。

负责：

- Scene Orchestration Engine
- Scene Contract 标准
- zone/block/action 统一标准
- scene resolver 框架
- layout orchestrator 框架
- capability injector 框架
- contract builder
- scene registry 机制
- snapshot / verify / governance

#### 3.1.3 `smart_construction_scene`

定位：施工行业场景内容模块。

负责：

- 施工行业 scene profiles
- 行业 block 语义配置
- 页面优先级策略
- 行业增强能力注入配置
- 行业场景下 action promotion 规则
- 模型与场景绑定规则

## 4. 场景编排层在整体链路中的职责划分

为防止层次串味，必须明确四层职责。

### 4.1 原生结构解析层职责

回答：`原生页面中有什么结构？`

负责：

- Odoo 原生 view 合并结果解析
- header / group / notebook / chatter / x2many / search / kanban 等结构标准化
- 字段元数据提取
- 原生按钮与动作元信息提取
- modifiers / domain / context / widget / options 提取

输出：`Normalized Native Structure`

### 4.2 业务层职责

回答：`业务规则是否允许？`

负责：

- 模型规则
- 生命周期规则
- 状态推进规则
- 权限规则
- 动作执行规则
- 可执行性 verdict
- 禁用原因 verdict

输出：

- `Permission Verdicts`
- `Action Verdicts`
- `Business State Summary`

### 4.3 场景编排层职责

回答：`针对当前用户场景，页面该如何组织与增强？`

负责：

- scene 识别
- 结构重组
- 信息优先级编排
- 动作面整理
- 增强能力挂载
- Scene Contract 输出

输出：`Scene Contract`

### 4.4 前端渲染层职责

回答：`如何根据 Scene Contract 进行通用渲染与交互？`

负责：

- Page Renderer
- Zone Renderer
- Block Renderer
- Action Surface Renderer
- 表单交互与保存
- 状态展示与反馈
- 插槽式增强渲染

输入：`Scene Contract`

## 5. 设计目标

场景编排层必须同时满足以下目标：

### 5.1 继承原生结构能力

最大程度复用 Odoo 原生页面结构，不重复定义基础页面骨架。

### 5.2 支撑产品化页面组织

能够将同一模型在不同场景下组织成不同页面重点，而不是一比一照搬原生页面。

### 5.3 对前端形成唯一输入

前端不得再消费原始 XML、零散字段或页面猜测逻辑，Scene Contract 必须成为唯一事实来源。

### 5.4 支撑多行业扩展

编排引擎和契约标准必须保持平台化，行业模块只需要提供内容和策略。

### 5.5 可治理、可验证、可回归

必须支持版本化、快照导出、shape guard、样本回归和 coverage 审计。

## 6. 核心设计原则

### 6.1 结构继承原则

凡原生视图已定义的字段关系、分组关系、分页关系、动作关系，优先继承。

### 6.2 场景重组原则

继承不等于照搬。场景编排层必须根据页面目标进行语义重组和展示层级编排。

### 6.3 后端解释原则

编排职责必须在后端完成，前端不得承担页面意图推理和结构编排责任。

### 6.4 契约唯一原则

Scene Contract 是前端唯一输入。前端不得自行拼接 scene，不得自定义冲突页面结构。

### 6.5 增强外挂原则

AI 建议、风险预警、下一步动作、摘要指标等能力，必须通过注入机制挂载。

### 6.6 业务判定外置原则

场景编排层只能消费业务判定结果，不得重新计算业务规则和权限规则。

### 6.7 平台机制与行业内容分离原则

平台负责机制，行业负责内容，禁止平台层直接固化行业页面策略。

## 7. 场景编排层完整能力模型

建议将场景编排层划分为五个核心子能力模块。

### 7.1 Scene Resolver（场景解析器）

#### 职责

确定当前请求对应哪个 `scene_key` 以及 scene 的目标和模式。

#### 输入

- model
- view_type
- menu / action / route 来源
- context
- 当前用户角色
- record state
- scene hint

#### 输出

- `scene_key`
- `scene_type`
- `page_goal`
- `interaction_mode`
- `layout_mode`
- `capability_scope`

#### 约束

- 不负责布局细节
- 不负责 block 生成
- 只负责识别当前进入哪个场景

### 7.2 Structure Mapper（结构映射器）

#### 职责

把标准化原生结构映射为可编排的基础 block 和基础 zone。

#### 输入

- normalized native structure
- field metadata
- native action metadata
- native relation metadata
- permission verdict hints

#### 输出

- `base_zones`
- `base_blocks`
- `block_field_mapping`
- `block_action_mapping`
- `relation_mapping`

#### 约束

- 不做行业特定排序
- 不做最终页面布局重排
- 只做“原生结构 → 基础语义块”的统一映射

### 7.3 Layout Orchestrator（布局编排器）

#### 职责

根据 scene profile 和上下文，决定 zone 顺序、block 摆放、显示层级和折叠策略。

#### 输入

- scene profile
- base zones / blocks
- role scope
- record state
- importance rules

#### 输出

- `final_zone_order`
- `final_block_placement`
- `display_priority`
- `collapse_policy`
- `tab_condense_policy`

#### 约束

- 不得篡改 block 的业务含义
- 不得推翻业务层的 verdict
- 只负责展示组织，不负责规则裁决

### 7.4 Capability Injector（能力注入器）

#### 职责

将外挂式增强能力挂入最终页面契约。

#### 输入

- scene capability config
- extension registry
- record context
- permission verdicts
- diagnostics / recommendation payloads

#### 输出

- `injected_blocks`
- `injected_actions`
- `extension_metadata`
- `injection_trace`

#### 约束

- 注入只能新增，不得覆盖基础原生语义
- 注入只能挂载到标准 zone / action surface
- 不得绕过业务权限结论

### 7.5 Scene Contract Builder（契约构建器）

#### 职责

将所有中间结果整合为最终 Scene Contract。

#### 输入

- scene metadata
- final zones
- final blocks
- action surface
- permissions
- record payload
- diagnostics

#### 输出

- `Scene Contract`

#### 约束

- 必须统一 version、shape、diagnostics
- 必须输出平台标准 contract schema
- 不允许各行业模块各自发明顶层字段结构

## 8. 输入模型设计

场景编排层的输入必须标准化，不允许直接接收零散临时数据。

### 8.1 Native Structure Input

来源：原生结构解析层。

内容包括：

- view_type
- header
- button_box
- notebook/page
- field groups
- relations
- chatter
- ribbon
- statusbar
- search metadata
- kanban metadata

### 8.2 Field Meta Input

来源：字段元数据层。

内容包括：

- field name
- type
- string
- required
- readonly
- invisible
- domain
- widget
- options
- help
- placeholder

### 8.3 Action Meta Input

来源：动作元数据层。

内容包括：

- native buttons
- action buttons
- object buttons
- stat buttons
- smart buttons
- toolbar actions
- row/card actions

### 8.4 Permission Verdict Input

来源：业务层 / 权限层。

内容包括：

- can_read
- can_edit
- can_create
- can_delete
- enabled_actions
- disabled_actions
- reason_if_disabled
- page_mode verdict
- record state summary

### 8.5 Scene Profile Input

来源：行业模块或场景配置层。

内容包括：

- scene_key
- scene_type
- page_goal
- layout_mode
- priority_rules
- zone_policies
- action_policies
- extension_policies

### 8.6 Record Context Input

来源：记录上下文层。

内容包括：

- record data
- record id
- record status/stage
- role relation
- business summary
- optional derived metrics

## 9. Scene Profile 标准设计

Scene Profile 是行业内容层向平台编排引擎提供的标准配置对象。

### 9.1 标准结构

```json
{
  "scene_key": "project.overview.manager",
  "scene_type": "detail",
  "target_model": "project.project",
  "page_goal": "帮助项目经理快速查看项目状态并执行关键动作",
  "interaction_mode": "inspect_and_act",
  "layout_mode": "summary_detail_dual_column",
  "priority_rules": {},
  "zone_policies": {},
  "action_policies": {},
  "extension_policies": {}
}
```

### 9.2 必填字段

- `scene_key`
- `scene_type`
- `target_model`
- `page_goal`
- `interaction_mode`
- `layout_mode`

### 9.3 priority_rules

用于定义：字段前置、block 前置、关系区重要度、默认展开/折叠策略。

### 9.4 zone_policies

用于定义：zone 顺序、zone 启用/禁用、zone 合并、zone tab 化、zone 默认显示策略。

### 9.5 action_policies

用于定义：primary action 提升规则、secondary 收纳规则、danger action 规则、recommended action 规则。

### 9.6 extension_policies

用于定义：允许注入哪些扩展 block / action、注入位置、注入条件、注入优先级。

## 10. Zone / Block / Action 平台标准

### 10.1 Zone 标准

平台层必须统一固定标准 zone 名称：

- `header_zone`
- `summary_zone`
- `detail_zone`
- `relation_zone`
- `action_zone`
- `collaboration_zone`
- `insight_zone`
- `attachment_zone`

约束：

- 行业模块不得新增平行顶层 zone 名称体系
- 允许在平台标准 zone 内组合不同 block
- zone 的新增必须走平台 contract 演进流程

### 10.2 Block 类型标准

平台层建议 v1 固定支持：

- `title_block`
- `status_block`
- `action_bar_block`
- `stat_button_block`
- `field_group_block`
- `notebook_block`
- `relation_table_block`
- `relation_card_block`
- `relation_tab_block`
- `chatter_block`
- `activity_block`
- `attachment_block`
- `timeline_block`
- `ribbon_block`
- `risk_alert_block`
- `ai_recommendation_block`
- `next_action_block`
- `summary_metrics_block`

约束：

- 平台定义 block 类型语义
- 行业模块可以定义 block key，但必须映射到平台 block type
- 不允许行业模块创造与前端耦合的 block type

### 10.3 Action Surface 标准

平台统一输出以下动作分组：

- `primary_actions`
- `secondary_actions`
- `contextual_actions`
- `danger_actions`
- `recommended_actions`

约束：

- 前端不得自行决定动作重要性层级
- 行业模块只能通过 `action_policies` 调整动作归组
- 动作分组标准必须统一进入 contract

## 11. Scene Contract 顶层标准

Scene Contract 必须由平台层定义统一 schema。

### 11.1 标准顶层结构

```json
{
  "scene": {},
  "page": {},
  "zones": [],
  "blocks": {},
  "actions": {},
  "permissions": {},
  "record": {},
  "extensions": {},
  "diagnostics": {}
}
```

### 11.2 顶层字段职责

#### `scene`

场景元信息：scene_key、scene_type、page_goal、interaction_mode、layout_mode、scene_version。

#### `page`

页面基础属性：model、record_id、view_type、title_field、subtitle_fields、page_status。

#### `zones`

页面区块顺序与组织定义。

#### `blocks`

所有 block 的字典对象。

#### `actions`

动作面定义。

#### `permissions`

页面级与动作级 verdict。

#### `record`

当前页面需要的记录数据与摘要数据。

#### `extensions`

本次注入的增强能力信息。

#### `diagnostics`

调试信息、来源信息、版本信息、生成轨迹。

## 12. 平台层与行业层的归属边界

### 12.1 必须属于平台层的内容

#### A. 编排引擎框架

- Scene Resolver 框架
- Structure Mapper 框架
- Layout Orchestrator 框架
- Capability Injector 框架
- Scene Contract Builder

#### B. 契约标准

- Scene Contract schema
- scene/page/zones/blocks/actions/permissions 顶层结构
- zone 标准
- block type 标准
- action surface 标准

#### C. 注册与扩展机制

- scene registry 框架
- extension registry 框架
- mapper / injector 扩展点
- layout policy hook

#### D. 治理与验证

- contract version
- scene version
- block catalog
- shape guard
- snapshot guard
- sample compare
- coverage matrix

#### E. 平台通用编排流程

- 统一执行顺序
- 标准 diagnostics
- 契约输出管线

### 12.2 必须属于行业层的内容

#### A. 具体 scene profiles

例如：

- `project.initiation.create`
- `project.overview.manager`
- `contract.execution.detail`
- `cost.ledger.control`

#### B. 行业优先级策略

例如：

- 项目经理优先看进度与风险
- 领导优先看摘要与预警
- 立项场景优先最小字段集

#### C. 行业增强注入策略

例如：

- 风险提醒挂入 `insight_zone`
- 下一步动作挂入 `action_zone`
- 成本偏差摘要挂入 `summary_zone`

#### D. 行业 block 语义映射

例如：

- `project_summary_block`
- `contract_fulfillment_block`
- `cost_warning_block`

但最终必须映射到平台 block type。

#### E. 行业 action promotion 规则

例如：

- 哪些动作为 primary
- 哪些动作为 recommended
- 哪些动作应隐藏或后置

### 12.3 严禁跨界的情况

#### 平台层严禁

- 直接写死施工行业页面策略
- 直接定义施工行业 scene
- 直接固化行业注入位置和行业优先级

#### 行业层严禁

- 发明新的顶层 Scene Contract schema
- 发明新的顶层 zone 体系
- 绕过平台 action surface 体系
- 绕过平台 shape guard 和 snapshot 机制
- 输出前端专属组件名或 CSS 细节

## 13. 运行流程标准

场景编排层统一按以下顺序运行：

### Step 1：Scene Resolve

根据 model / route / menu / action / context / role 解析当前 scene。

### Step 2：接收 Native Structure

从结构解析层获取标准化原生结构。

### Step 3：Build Base Blocks

将 native structure 映射为基础 block 和初始 zone。

### Step 4：Apply Scene Policies

应用 scene profile 中的 priority / zone / action 策略。

### Step 5：Inject Extensions

根据能力注入策略注入增强 block / action。

### Step 6：Build Action Surface

将原生动作与扩展动作整理为标准 action surface。

### Step 7：Build Scene Contract

构建最终 Scene Contract，附加 diagnostics 和版本信息。

### Step 8：Run Guards / Snapshot

对 contract 做 shape guard，必要时输出 snapshot 或对比样本。

## 14. 关键约束清单

以下约束必须作为开发红线。

### 14.1 前端不得再猜测页面意图

前端不得自行判断：

- 这是 summary 还是 detail
- 哪个 block 应前置
- 哪个动作应为主动作
- 哪个 zone 是否启用

这些必须由 Scene Contract 明确输出。

### 14.2 场景编排层不得重新计算业务规则

编排层不得自行判断：

- 是否可审批
- 是否可删除
- 是否可编辑
- 当前记录状态是否合法

只能消费 verdict。

### 14.3 行业模块不得破坏平台 contract

行业模块不能：

- 自定义顶层 contract 字段
- 改写平台 zone 语义
- 输出不合规 block type
- 绕过平台治理链

### 14.4 平台层不得污染行业策略

平台层不能：

- 写死“项目经理必须看什么”
- 写死“合同页风险必须放哪里”
- 写死某行业特定信息优先级

### 14.5 能力注入只能增量挂载

注入能力只能：

- 新增 block
- 新增 action
- 调整已允许的展示编排

不能：

- 篡改原生业务字段含义
- 覆盖业务 verdict
- 改写基础 contract 主结构

## 15. 目录结构建议

### 15.1 平台层：`smart_scene`

```text
addons/smart_scene/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── scene_registry.py
│   ├── scene_contract_builder.py
│   ├── scene_resolver.py
│   ├── structure_mapper.py
│   ├── layout_orchestrator.py
│   ├── capability_injector.py
│   └── diagnostics_service.py
├── services/
│   ├── scene_engine.py
│   ├── contract_guard.py
│   ├── snapshot_service.py
│   └── coverage_service.py
├── schemas/
│   ├── scene_contract_schema.py
│   ├── block_catalog.py
│   ├── zone_catalog.py
│   └── action_surface_schema.py
├── registry/
│   ├── scene_profile_registry.py
│   ├── block_provider_registry.py
│   └── extension_provider_registry.py
├── tests/
│   ├── test_scene_contract_shape.py
│   ├── test_scene_registry.py
│   ├── test_action_surface_shape.py
│   └── test_snapshot_compare.py
└── docs/
```

### 15.2 行业层：`smart_construction_scene`

```text
addons/smart_construction_scene/
├── __init__.py
├── __manifest__.py
├── profiles/
│   ├── project_scenes.py
│   ├── contract_scenes.py
│   ├── cost_scenes.py
│   └── settlement_scenes.py
├── policies/
│   ├── priority_rules.py
│   ├── zone_policies.py
│   ├── action_policies.py
│   └── extension_policies.py
├── providers/
│   ├── project_block_provider.py
│   ├── contract_block_provider.py
│   ├── cost_block_provider.py
│   └── recommendation_provider.py
├── mappings/
│   ├── model_scene_mapping.py
│   └── role_scene_mapping.py
├── tests/
│   ├── test_project_scene_profiles.py
│   ├── test_action_policies.py
│   └── test_extension_injection.py
└── docs/
```

## 16. 当前阶段建议的最小落地范围

为避免一口吞鲸，建议分三阶段推进。

### Phase 1：平台编排闭环

先完成：

- Scene Contract 标准
- Scene Resolver
- Structure Mapper
- Layout Orchestrator
- 基础 Contract Builder
- 基础 shape guard

覆盖对象：

- form detail scene
- list scene

### Phase 2：行业场景接入

施工行业先落：

- 项目立项 scene
- 项目总览 scene
- 合同详情 scene
- 成本控制 scene

同时建立：

- priority rules
- action policies
- basic extension policies

### Phase 3：增强与治理

再补：

- AI / 风险 / 下一步动作注入
- snapshot compare
- sample scene regression
- coverage matrix
- scene contract verify 链

## 17. 验证与治理要求

场景编排层必须纳入系统治理链。

### 17.1 必须版本化

至少包含：

- `contract_version`
- `scene_version`
- `block_catalog_version`

### 17.2 必须有 shape guard

至少校验：

- scene shape
- zone shape
- block shape
- action shape
- permissions shape

### 17.3 必须有 snapshot guard

关键 scene contract 必须导出快照并可比对。

### 17.4 必须有样本回归

至少对以下页面保留回归样本：

- 一个简单 form
- 一个复杂 form
- 一个 tree/list
- 一个 search/filter scene
- 一个带增强注入的 scene

### 17.5 必须有 coverage 视图

可输出：

- scene profile 覆盖情况
- block type 覆盖情况
- action surface 覆盖情况
- extension coverage 情况

## 18. 推荐的系统级定义

建议将以下文字正式写入系统架构文档：

场景编排层是位于原生结构解析层与前端渲染层之间的后端编排引擎。平台层负责提供统一的编排机制、契约标准、扩展点与治理能力；行业模块负责提供具体场景定义、页面优先级策略、行业语义映射和增强能力装配策略。场景编排层的最终输出是前端唯一消费的 Scene Contract。

## 19. 最终口径

以后系统中的页面生成逻辑，统一采用如下表述：

`原生视图 → 结构解析 → 场景编排 → Scene Contract → 前端通用渲染`

不再采用：

`原生视图 → 前端自己猜着画`

## 20. 一句话收口

场景编排层不是行业页面模板堆，也不是底层内核附属品；它是平台提供引擎、行业提供内容的中间能力层，是系统从“能解析页面”走向“能交付产品页面”的关键桥梁。

