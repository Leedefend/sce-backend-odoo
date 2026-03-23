# Payment Slice Five-Layer Freeze

## 冻结对象

- 切片：`项目创建 -> 驾驶舱 -> 计划 -> 执行 -> 成本记录 -> 付款记录 -> 付款汇总`
- 原则：五层职责固定，不允许跨层合并
- 状态：`正式冻结`

## L1 Model Layer

- `project.project`
- `payment.request`

### 冻结口径

- `payment.request` 作为付款记录主载体
- `project.project` 作为项目归属锚点
- 只复用 `draft payment.request` 记录能力，不进入 submit/approve/done 审批语义
- 不引入新的“大付款主模型”

## L2 Domain Capability Layer

- `create_payment_entry`
- `fetch_payment_list_block`
- `fetch_payment_summary_block`

### 冻结口径

- 付款录入只创建最小 draft `payment.request`
- 付款列表与汇总只基于项目过滤后的 `payment.request(type=pay)`
- 汇总只统计当前切片内项目付款记录，不引入合同、审批、结算

## L3 Scene Layer

- `project.execution`
- `cost.tracking`
- `payment.enter`
- `payment.block.fetch`
- `payment.record.create`

### 冻结口径

- 主链固定为：
  - `project.initiation -> project.dashboard -> project.plan_bootstrap -> project.execution -> cost.tracking -> payment`
- `project.execution` / `cost.tracking` 只负责暴露进入付款切片的 next_action
- `payment.record.create` 只负责最小写入，不在 scene 层拼审批或合同规则

## L4 Contract Layer

- `payment` entry contract
- `payment_entry` block contract
- `payment_list` block contract
- `payment_summary` block contract
- `execution -> payment` action contract
- `cost -> payment` action contract

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

- 前端只消费 `payment_entry / payment_list / payment_summary / next_actions`
- 前端不计算付款汇总
- 前端不推导合同、审批、发票、结算语义

## 冻结结论

- FR-4 付款切片五层边界已经固定，可作为正式冻结切片继续发布。
