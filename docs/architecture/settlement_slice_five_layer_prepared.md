# Settlement Slice Five-Layer Prepared

## Prepared 对象

- 切片：`execution/cost/payment -> settlement summary`
- 原则：复用优先，只读聚合，前端零计算
- 状态：`Prepared`

## L1 Model Layer

- `project.project`
- `account.move`
- `payment.request`

### Prepared 口径

- 不新增模型
- 成本来源固定为 `account.move`
- 付款来源固定为 `payment.request`
- `project.project` 作为项目归属锚点

## L2 Domain Capability Layer

- `fetch_settlement_summary`

### Prepared 口径

- 后端按 `project_id` 聚合成本与付款
- 输出只读汇总：
  - `total_cost`
  - `total_payment`
  - `delta`
  - `currency_name`
- 不引入合同、审批、发票、税务或分析逻辑

## L3 Scene Layer

- `project.execution`
- `cost.tracking`
- `payment`
- `settlement.enter`
- `settlement.block.fetch`

### Prepared 口径

- `execution/cost/payment` 只负责增加进入结算的 `next_action`
- `settlement.enter` 只返回 scene-ready contract
- `settlement.block.fetch` 只返回单一结算 block
- 不在 L3 拼接复杂业务规则

## L4 Contract Layer

- `settlement` entry contract
- `settlement_summary` block contract
- `execution -> settlement` action contract
- `cost -> settlement` action contract
- `payment -> settlement` action contract

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

- 前端只消费 `settlement_summary`
- 所有汇总和差额都由后端计算
- 不增加图表、趋势、多维分析

## 复用审计结论

### 已复用

- 模型：`account.move`、`payment.request`
- 场景承载模式：`BaseSceneEntryOrchestrator`
- 页面承载：`ProjectManagementDashboardView.vue`
- 汇总来源：FR-3 成本 adapter 与 FR-4 付款 adapter

### 最小新增

- `SettlementSliceService`
- `SettlementSliceSummaryBuilder`
- `SettlementSliceContractOrchestrator`
- `settlement.enter` / `settlement.block.fetch`

## Prepared 结论

- FR-5 是只读结算切片，不是合同/财务/审批系统。
- 本轮只把成本与付款事实收口为项目级简单汇总结果。
