# Unified Page Contract v2+ 完整架构设计（建议版）

面向：Odoo 下一代多端统一 UI Runtime

目标：建立可治理、可演进、可增量更新、可多端适配的企业级 Contract-Driven UI 架构

Version: Draft 2.1

Date: 2026-05-01

## 0. 规范级别说明

本文档是 `UnifiedPageContract v2+` 的架构设计与协议冻结依据。

后续 JSON Schema、后端 assembler、前端 runtime、snapshot guard 都必须以本文档为上位约束。

关键术语约束：

- `MUST` / 必须：不满足即不允许进入默认协议路径。
- `SHOULD` / 应该：推荐实现；若暂缓，必须有兼容说明和退出计划。
- `MAY` / 可以：可选能力，不得影响核心协议稳定性。

协议定位：

```text
UnifiedPageContract v2+ = UI Runtime IR + Governed Patch Protocol
```

不是：

```text
页面 JSON
低代码执行器
前端规则 VM
业务工作流引擎
```

## 1. 总体目标

`UnifiedPageContract` 不再只是：

```text
页面接口
```

而是：

```text
企业级 UI Runtime Protocol
```

其职责是：

- 后端统一拥有业务语义。
- 前端只负责渲染与交互分发。
- 多端共享业务规则。
- Contract 可增量更新。
- Contract 可治理。
- Contract 可追踪。
- Contract 可演进。
- Contract 可兼容。

最终形成：

```text
Backend Semantic Engine
+
Frontend Runtime Renderer
```

架构。

## 2. 核心原则

### 2.1 One Canonical Contract

前端最终只消费一种标准协议：

```json
{
  "pageInfo": {},
  "layoutContract": {},
  "statusContract": {},
  "actionContract": {},
  "dataContract": {},
  "runtimeContract": {},
  "meta": {}
}
```

旧协议只能存在于：

```json
{
  "meta": {
    "compat": {}
  }
}
```

内部。

### 2.2 Backend Owns Semantics

前端禁止推导：

- permission
- role
- visible
- readonly
- required
- action availability
- business workflow
- linkage rule
- lifecycle

前端职责：

```text
render
input
dispatch
local feedback
```

后端职责：

```text
semantic authority
```

### 2.3 Contract Is IR

`UnifiedPageContract` 本质是：

```text
UI Intermediate Representation
```

类似：

- Compiler IR
- React Fiber Tree
- Flutter Render Object
- Virtual DOM
- Low-Code Schema

因此：

- Contract 必须稳定。
- ID 必须稳定。
- Patch 必须稳定。
- 生命周期必须稳定。

### 2.4 Multi-Terminal Same Semantics

允许不同：

- layout density
- component adapter
- responsive layout
- unsupported fallback
- visual behavior

禁止不同：

- business semantics
- permission logic
- field linkage
- action routing
- data meaning

## 3. 总体架构

```text
+---------------------------+
| Odoo Model / ORM / ACL    |
+-------------+-------------+
              |
+-------------v-------------+
| Native Parse Layer         |
| view/action/modifier parse |
+-------------+-------------+
              |
+-------------v-------------+
| Semantic Governance Layer  |
| normalize / schema / diff  |
+-------------+-------------+
              |
+-------------v-------------+
| Scene Orchestration Layer  |
| composition / page model   |
+-------------+-------------+
              |
+-------------v-------------+
| Contract Assembler         |
| UnifiedPageContract v2+    |
+-------------+-------------+
              |
+-------------v-------------+
| Client Trimming Layer      |
| pc/h5/mini-program         |
+-------------+-------------+
              |
+-------------v-------------+
| Frontend Runtime           |
| Renderer + Patch Engine    |
+---------------------------+
```

## 4. Top-Level Contract

### 4.1 Shape

```json
{
  "pageInfo": {},
  "layoutContract": {},
  "statusContract": {},
  "actionContract": {},
  "dataContract": {},
  "runtimeContract": {},
  "meta": {}
}
```

必选顶层字段必须固定。当前 v2 仅允许一个受控可选顶层扩展：
`formStructureContract`。

`formStructureContract` 只表达产品级表单结构编排契约，不直接承载业务事实，
也不得作为任意新增平级顶层协议的先例。未来新增能力默认仍必须进入既有子契约。

## 5. PageInfo

### 5.1 Responsibility

`PageInfo` 描述页面身份与运行模式。

不允许包含：

- widget definition
- permission details
- record data
- runtime patch

### 5.2 Shape

```json
{
  "pageId": "project.form",
  "sceneKey": "project.intake",
  "pageName": "Project Form",
  "model": "project.project",
  "viewType": "form",
  "layoutType": "form",
  "renderMode": "governed",
  "contractVersion": "2.1.0",
  "clientType": "web_pc"
}
```

## 6. LayoutContract

### 6.1 Responsibility

`LayoutContract` 只负责：

```text
结构
```

包括：

- container hierarchy
- widget placement
- layout type
- terminal adaptation hints
- visual grouping

禁止拥有：

- permission
- business rule
- readonly
- required
- data value

### 6.2 Shape

```json
{
  "pageId": "project.form",
  "layoutType": "form",
  "adaptMode": "pc",
  "containerTree": [],
  "layoutHints": {},
  "componentRegistry": {}
}
```

### 6.3 Container Model

```json
{
  "containerId": "main.basic",
  "containerType": "group",
  "title": "Basic",
  "span": 12,
  "styleToken": "defaultGroup",
  "children": [],
  "widgetList": []
}
```

### 6.4 Widget Model

```json
{
  "widgetId": "field.name",
  "widgetType": "input",
  "fieldCode": "name",
  "label": "Name",
  "span": 6,
  "componentKey": "sc.input.text",
  "capabilities": [
    "clearable",
    "searchable"
  ],
  "componentConfig": {}
}
```

### 6.5 Capability Protocol

禁止：

```json
{
  "componentConfig": {
    "anything": "everything"
  }
}
```

无限膨胀。

必须引入：

```json
{
  "capabilities": []
}
```

用于声明：

- virtual scroll
- sortable
- resizable
- editable
- drag
- aggregate
- tree-expand
- filterable

### 6.6 Component Registry

必须存在组件注册中心：

```json
{
  "componentRegistry": {
    "sc.input.text": {
      "version": "1.0",
      "adapter": {
        "web_pc": "ElInput",
        "wx_mini": "WxInput"
      }
    }
  }
}
```

避免：

```text
widgetType explosion
```

## 7. StatusContract

### 7.1 Responsibility

`StatusContract` 负责：

- visible
- readonly
- disabled
- required
- placeholder
- auth
- reasonCode

禁止：

- layout
- business action execution
- data value

### 7.2 Shape

```json
{
  "globalStatus": {},
  "containerStatus": [],
  "widgetStatus": [],
  "buttonStatus": [],
  "selectorStatus": []
}
```

### 7.3 Selector Status

为避免状态爆炸，支持 selector 级状态：

```json
{
  "selector": "finance.*",
  "readonly": true
}
```

支持：

- container inheritance
- batch status
- tree propagation
- virtualized status

避免：

```text
10 万 widget status patch
```

### 7.4 ReasonCode

必须由后端定义稳定 code：

```json
{
  "reasonCode": "PROJECT_LOCKED"
}
```

前端禁止生成业务 reason。

## 8. ActionContract

### 8.1 核心原则

`ActionContract`：

```text
只负责事件声明
```

绝不负责：

```text
业务执行引擎
```

禁止演化成：

- BPMN
- Rule Engine
- Workflow VM
- JSON Logic Runtime

### 8.2 Shape

```json
{
  "actionRuleList": []
}
```

### 8.3 Action Rule

```json
{
  "actionId": "project.name.change",
  "triggerType": "change",
  "sourceWidgetId": "field.name",
  "dispatchMode": "server",
  "targetScope": "page",
  "refreshMode": "partial"
}
```

### 8.4 Dispatch Model

前端：

```text
collect context
-> dispatch actionId
```

后端：

```text
evaluate semantics
-> generate patch
```

前端不解释业务逻辑。

### 8.5 Action Lifecycle

```text
beforeDispatch
-> dispatch
-> serverEvaluate
-> patchMerge
-> renderCommit
-> postEffect
```

必须标准化。

### 8.6 Dependency Graph

必须建立：

```text
field dependency DAG
```

否则 onchange 链会失控。

示例：

```json
{
  "dependencyGraph": {
    "field.name": [
      "field.display_name",
      "field.code"
    ]
  }
}
```

## 9. DataContract

### 9.1 Responsibility

只负责：

```text
renderable data
```

禁止：

- permission
- readonly
- linkage
- workflow

### 9.2 Shape

```json
{
  "mainData": {},
  "tableRows": {},
  "relationRows": {},
  "dictData": {},
  "pagination": {},
  "dataSource": {},
  "dataMeta": {}
}
```

### 9.3 Data Source

预留：

```json
{
  "dataSource": {
    "project_list": {
      "query": "project.search",
      "cachePolicy": "etag",
      "consistency": "eventual",
      "subscription": true
    }
  }
}
```

为未来能力做准备：

- realtime
- websocket
- streaming
- AI context
- BI dashboard

## 10. RuntimeContract

这是 v2+ 最建议新增的部分，否则很多 runtime 行为会污染其它 contract。

### 10.1 Responsibility

负责：

- patch strategy
- cache policy
- optimistic update
- debounce
- retry
- render strategy
- hydration
- lazy loading
- virtual scroll

### 10.2 Shape

```json
{
  "patchStrategy": "incremental",
  "cachePolicy": "etag",
  "optimistic": true,
  "lazyContainer": [],
  "virtualization": {},
  "retryPolicy": {}
}
```

## 11. Incremental Update Protocol

### 11.1 Core Principle

所有交互：

```text
返回 patch
优先于 full contract
```

### 11.2 Partial Update

```json
{
  "updateType": "partial",
  "layoutPatch": {},
  "statusPatch": {},
  "dataPatch": {},
  "runtimePatch": {},
  "meta": {}
}
```

### 11.3 Full Update

```json
{
  "updateType": "full",
  "contract": {}
}
```

### 11.4 Patch Engine

真正核心不是 renderer，而是：

```text
Contract Diff Engine
```

必须具备：

- structural diff
- selector merge
- reactive propagation
- dependency scheduling
- minimal patch
- optimistic rollback
- patch ordering

## 12. ID Governance

### 12.1 必须稳定

以下 ID 永远稳定：

- pageId
- sceneKey
- containerId
- widgetId
- fieldCode
- btnId
- actionId
- dataKey

### 12.2 ID 禁止携带业务变化

禁止：

```text
field.price.admin
field.price.user
```

应该：

```text
field.price
+ status contract
```

## 13. Multi-Terminal Strategy

### 13.1 Supported Client

```text
web_pc
wx_mini
harmony_h5
mobile_app
```

`mobile_app` 是未来扩展位。Batch-A 可先冻结前三端，Batch-G 再决定是否把 `mobile_app` 纳入首批 guard。

### 13.2 Client Trimming

允许：

- component adapter
- layout density
- unsupported fallback
- mobile collapse

禁止：

- business semantic change
- permission divergence
- action divergence

## 14. Frontend Runtime Architecture

### 14.1 Runtime Core

```text
Contract Store
+ Patch Engine
+ Renderer
+ Action Dispatcher
+ Dependency Graph
+ Reactive Scheduler
```

### 14.2 Frontend Must Not Own

前端禁止：

- role infer
- business infer
- permission infer
- linkage infer
- workflow infer

否则多端一定分裂。

## 15. Cache Strategy

### 15.1 ETag

所有 contract 必须支持：

```json
{
  "etag": "xxx"
}
```

### 15.2 Snapshot

支持：

```json
{
  "snapshotId": "xxx"
}
```

用于：

- undo
- history replay
- debug
- trace
- collaboration

## 16. Traceability

所有 roundtrip 必须包含：

```json
{
  "traceId": "",
  "requestId": "",
  "actionId": "",
  "snapshotId": ""
}
```

否则无法治理。

## 17. Governance Layer

### 17.1 必须存在 Shape Guard

所有 Contract 必须经过：

- schema validation
- enum validation
- compatibility validation
- forbidden field validation

### 17.2 Forbidden Drift

禁止：

```text
frontend private field
```

进入标准 contract，否则 schema 会逐渐腐烂。

## 18. Compatibility Strategy

### 18.1 Legacy Compatibility

旧协议必须映射进入 v2+：

```text
scene_contract_v1
page_orchestration_v1
ui.contract
api.onchange
```

### 18.2 Compatibility Boundary

兼容逻辑必须：

```text
只存在 governance layer
```

前端不得处理 legacy protocol。

## 19. Future AI Integration

### 19.1 AI 不直接操作 DOM

AI 应操作：

```text
UnifiedPageContract
```

而不是：

```text
HTML
```

### 19.2 AI Capability

未来 AI 可以：

- semantic form fill
- workflow assist
- contract inspection
- layout generation
- action simulation
- dependency analysis

因为 contract 已语义化。

## 20. 最大风险

### 20.1 Action Engine Explosion

最危险问题：

```text
ActionContract 演变成业务 DSL VM
```

会导致：

- debug hell
- version hell
- tracing hell
- async hell

必须禁止。

### 20.2 Component Schema Explosion

`componentConfig` 无限膨胀。

必须通过：

- capability governance
- component registry
- adapter layer

控制。

### 20.3 Patch Storm

大型页面会出现：

```text
status patch storm
```

必须通过：

- selector status
- inheritance
- batching
- virtualization

控制。

## 21. 推荐演进路线

### Phase 1

冻结：

- top-level schema
- ID rules
- patch protocol
- action lifecycle

### Phase 2

实现：

- governance layer
- diff engine
- patch merge
- selector status

### Phase 3

实现：

- realtime patch
- websocket sync
- optimistic update
- collaboration

### Phase 4

实现：

- AI semantic interaction
- auto orchestration
- semantic workflow assist

## 22. 最终定位

`UnifiedPageContract` 最终不是：

```text
页面 JSON
```

而是：

```text
Enterprise Semantic UI Runtime Protocol
```

它本质上是：

```text
UI Operating System IR
```

用于统一：

- Web
- Mini Program
- H5
- Mobile App
- AI Runtime
- Future Terminal

并保证：

```text
One Semantic Source of Truth
```

## 23. 协议生命周期

### 23.1 Contract Build Lifecycle

完整构建链路：

```text
native facts collected
-> semantic facts normalized
-> scene composed
-> unified contract assembled
-> client trimmed
-> shape guarded
-> snapshot recorded
-> frontend consumed
```

每一步必须有明确输入和输出，禁止跨层直接透传私有结构。

### 23.2 Runtime Interaction Lifecycle

所有交互必须遵循：

```text
frontend collect context
-> dispatch actionId
-> backend evaluate semantics
-> backend emit patch/full contract
-> frontend patch merge
-> dependency schedule
-> render commit
-> trace/snapshot update
```

前端可以做本地 loading、dirty、focus、toast 等 UI feedback，但不得改变业务结论。

### 23.3 Compatibility Lifecycle

旧协议兼容必须有完整生命周期：

```text
introduce
-> observe
-> default
-> deprecate
-> remove
```

`meta.compat` 只能服务迁移，不得成为新功能入口。

## 24. Schema Freeze Boundary

Batch-A 冻结时必须同时冻结：

- 必选顶层字段：`pageInfo/layoutContract/statusContract/actionContract/dataContract/runtimeContract/meta`
- 受控可选顶层扩展：`formStructureContract`、`workflowContract`
- ID 规则：稳定 ID 列表与禁止后缀规则
- Client enum：首批支持与延期支持列表
- Patch protocol：partial/full 与 patch operation enum
- Action lifecycle：标准阶段与前后端责任
- Component registry：`componentKey` 与 adapter 约束
- Capability protocol：能力声明和禁止万能 `componentConfig`
- Selector status：selector patch 与继承规则
- Trace/snapshot：最小必填字段
- Anti-DSL VM：禁止字段和静态 guard 规则

未冻结前，不允许进入后端 assembler 实现。

`workflowContract` 的冻结边界：

- 它是后端业务 workflow service 对单条记录的投影，不是通用 assembler 从 XML 按钮或前端上下文推导出的状态。
- `workflowContract.availableActions` 是表单工作流按钮显示、禁用和去重的权威输入；`actionContract` 可以承载普通 UI 动作，但不得覆盖工作流可执行性结论。
- `workflowContract.evidenceGate` 是用户可见前置条件说明；相同业务条件必须在对应 backend action method 中再次校验。
- `runtimeContract.workflowContract` 仅作为兼容镜像，不能成为独立事实源。
- 覆盖口径按自定义业务工作流表单计算；标准 Odoo 模型例外必须由专项 guard 显式列出。

## 25. Open Decisions

以下问题必须在 Batch-A 或 Batch-B 前拍板：

| Decision | Candidate | Recommendation |
| --- | --- | --- |
| `mobile_app` 是否首批进入 enum | 首批冻结 / 未来扩展位 | 未来扩展位，先冻结 `web_pc/wx_mini/harmony_h5` |
| `componentRegistry` 放置位置 | `layoutContract` / `runtimeContract` | 语义引用在 `layoutContract`，注册治理在 `runtimeContract` |
| `dependencyGraph` 放置位置 | `actionContract` / `runtimeContract` | Runtime control plane 归 `runtimeContract` |
| `selectorStatus` 放置位置 | `statusContract` / `runtimeContract` | 状态结果归 `statusContract`，选择器治理归 `runtimeContract` |
| AI suggestion 是否进入标准 contract | 进入 / 独立 envelope | 只允许进入非执行 suggestion envelope |

## 26. Guard Requirements

最小 guard 集合：

- Top-level shape guard
- Enum guard
- Stable ID guard
- No role/client suffix ID guard
- Anti-DSL VM guard
- Compat leakage guard
- Client trimming stable ID guard
- Patch operation allowlist guard
- Frontend private field guard
- Snapshot volatility normalization guard
- Workflow contract profile-method guard
- Workflow contract custom business coverage guard

任何 guard 失败，都不得将 v2+ 设为默认 frontend contract。
