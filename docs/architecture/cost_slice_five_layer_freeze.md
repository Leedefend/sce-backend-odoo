# Cost Slice Five-Layer Freeze

## 冻结对象

- 切片：`项目创建 -> 驾驶舱 -> 计划 -> 执行 -> 成本记录 -> 成本汇总`
- 原则：五层职责固定，不允许跨层合并
- 状态：`正式冻结`

## L1 Model Layer

- `project.project`
- `account.move`
- `account.move.line`
- `project.cost.code`

### 冻结口径

- `account.move` 作为成本记录主载体
- `project.project` 作为项目归属锚点
- `project.cost.code` 仅用于最小类别选择，不扩展预算语义
- 不引入新的“大成本主模型”

## L2 Domain Capability Layer

- `create_cost_entry`
- `fetch_cost_list_block`
- `fetch_cost_summary_block`

### 冻结口径

- 成本录入只创建最小 draft `account.move`
- 成本列表与汇总只基于项目过滤后的 `account.move`
- 汇总只统计当前切片内项目成本记录，不引入预算、分析、审批

## L3 Scene Layer

- `project.execution`
- `cost.tracking.enter`
- `cost.tracking.block.fetch`
- `cost.tracking.record.create`

### 冻结口径

- 主链固定为：
  - `project.initiation -> project.dashboard -> project.plan_bootstrap -> project.execution -> cost.tracking`
- `project.execution` 只负责暴露进入成本切片的 next_action
- `cost.tracking.record.create` 只负责最小写入，不在 scene 层拼业务规则

## L4 Contract Layer

- `cost.tracking` entry contract
- `cost_entry` block contract
- `cost_list` block contract
- `cost_summary` block contract
- `execution -> cost` action contract

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

- 前端只消费 `cost_entry / cost_list / cost_summary / next_actions`
- 前端不计算成本汇总
- 前端不推导预算/审批/合同/付款语义

## 冻结结论

- FR-3 成本切片五层边界已经固定，可作为正式冻结切片继续发布。
