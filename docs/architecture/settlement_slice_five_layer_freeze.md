# Settlement Slice Five-Layer Freeze

## 冻结对象

- 切片：`项目创建 -> 驾驶舱 -> 计划 -> 执行 -> 成本 -> 付款 -> 结算结果`
- 原则：五层职责固定，只读聚合固定在后端
- 状态：`正式冻结`

## L1 Model Layer

- `project.project`
- `account.move`
- `payment.request`

### 冻结口径

- 不新增模型
- 成本来源固定为 `account.move`
- 付款来源固定为 `payment.request`
- `project.project` 作为项目归属锚点

## L2 Domain Capability Layer

- `fetch_settlement_summary`

### 冻结口径

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

### 冻结口径

- 主链固定为：
  - `project.initiation -> project.dashboard -> project.plan_bootstrap -> project.execution -> cost.tracking -> payment -> settlement`
- `project.execution` / `cost.tracking` / `payment` 只负责暴露进入结算的 next_action
- `settlement.enter` 只返回 scene-ready contract
- `settlement.block.fetch` 只返回单一结算 block

## L4 Contract Layer

- `settlement` entry contract
- `settlement_summary` block contract
- `execution -> settlement` action contract
- `cost -> settlement` action contract
- `payment -> settlement` action contract

### 冻结口径

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

### 冻结口径

- 前端只消费 `settlement_summary`
- 所有汇总和差额都由后端计算
- 前端不增加图表、趋势、多维分析或其他业务推导

## 冻结结论

- FR-5 结算切片五层边界已经固定，可作为正式冻结切片继续发布。
