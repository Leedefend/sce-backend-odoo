# Payment Slice Five-Layer Prepared

## Prepared 对象

- 切片：`execution/cost -> payment entry -> payment list -> payment summary`
- 原则：复用优先，缺口最小新增
- 状态：`Prepared`

## L1 Model Layer

- `project.project`
- `payment.request`

### Prepared 口径

- `payment.request` 作为付款记录主载体
- `project.project` 作为项目归属锚点
- 仅复用 `draft` 创建能力，不进入 submit/approve/done 语义
- 不新建复杂 payment 主模型

## L2 Domain Capability Layer

- `create_payment_entry`
- `fetch_payment_list_block`
- `fetch_payment_summary_block`

### Prepared 口径

- 付款录入只创建最小 `draft payment.request`
- 付款列表与汇总只基于项目过滤后的 `payment.request(type=pay)`
- 汇总只统计当前切片内项目付款记录，不引入合同、审批、结算

## L3 Scene Layer

- `project.execution`
- `cost.tracking`
- `payment.enter`
- `payment.block.fetch`
- `payment.record.create`

### Prepared 口径

- 主链固定为：
  - `project.execution -> payment`
  - `cost.tracking -> payment`
- `project.execution` / `cost.tracking` 只负责暴露进入付款切片的 next_action
- `payment.record.create` 只负责最小写入，不在 scene 层拼审批/合同逻辑

## L4 Contract Layer

- `payment` entry contract
- `payment_entry` block contract
- `payment_list` block contract
- `payment_summary` block contract
- `execution -> payment` action contract
- `cost -> payment` action contract

### Prepared 口径

- scene entry 统一保持：
  - `project_id`
  - `scene_key`
  - `scene_label`
  - `state_fallback_text`
  - `title`
  - `summary`
  - `blocks`
  - `suggested_action`
  - `runtime_fetch_hints`
- runtime block 统一保持：
  - `project_id`
  - `block_key`
  - `block`
  - `degraded`

## L5 Frontend Layer

- 生命周期工作台
- Scene contract consumer

### Prepared 口径

- 前端只消费 `payment_entry / payment_list / payment_summary / next_actions`
- 前端不计算付款汇总
- 前端不推导合同、审批、发票、结算语义

## 复用审计结论

### 已复用

- 模型：`payment.request`
- 场景承载模式：`BaseSceneEntryOrchestrator`
- builder 模式：FR-3 的 entry/list/summary/next_actions 结构
- 页面承载：`ProjectManagementDashboardView.vue`

### 明确不复用

- `finance.payment_requests` 财务中心 scene
- `payment.request.submit/approve/execute` 旧审批 handler
- 旧 `payment.request` 全量表单的合同/结算/审批字段面

## Prepared 结论

- FR-4 付款切片以 `payment.request` 为唯一事实载体。
- 本轮只补项目生命周期链里的最小付款能力，不进入审批或财务闭环。
