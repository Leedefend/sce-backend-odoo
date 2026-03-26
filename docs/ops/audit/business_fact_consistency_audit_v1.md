# Business Fact Consistency Audit v1

## 目标

对项目驾驶舱与主线切片中的核心业务语义做一次事实源审计，避免同一语义在不同页面由不同模型或不同计算口径驱动。

本轮聚焦 5 类语义：

- `task progress`
- `cost`
- `payment`
- `settlement`
- `project lifecycle / execution milestone`

## 结论

当前系统的主要一致性问题不是“没有数据”，而是“同一语义被多个 service 用不同事实源计算”。

本轮结论分两类：

- 已收口：
  - 驾驶舱、成本页、结算页的成本金额与成本条数，已统一到 `project.cost.ledger first`
  - 驾驶舱进度与决策引擎进度，已统一到 `project.task.sc_state=done`
- 待继续收口：
  - `payment` 仍同时依赖 `payment.request / payment.ledger / sc.settlement.order`
  - `flow_map / completion` 仍混合使用 `lifecycle_state` 与业务事实判断

## 事实源矩阵

| 业务语义 | 当前唯一事实源目标 | 当前主要消费点 | 当前状态 | 说明 |
| --- | --- | --- | --- | --- |
| 任务完成数 | `project.task.sc_state` | `project_dashboard_service.py` / `project_decision_engine_service.py` / `project_progress_builder.py` | 已对齐 | 不再使用 `stage_id.fold` 推断完成态 |
| 执行进度百分比 | `project.task` 总数 + `sc_state=done` 数 | 驾驶舱摘要 / 决策引擎 / 进度块 | 已对齐 | 百分比必须由真实任务事实计算 |
| 成本金额 | `project.cost.ledger.amount` | 驾驶舱 / 成本页 / 结算页 / 决策引擎 | 已对齐 | `account.move` 仅作为 fallback |
| 成本记录条数 | `project.cost.ledger` 行数 | 成本页 / 驾驶舱 / 结算页 | 已对齐 | 不再让“金额来自 ledger、条数来自 move” |
| 付款金额 | `payment.request.amount` | 驾驶舱 / 付款页 / 结算页 / 决策引擎 | 基本对齐 | 仍需区分“申请事实”与“已支付事实” |
| 付款记录条数 | `payment.request` 行数 | 驾驶舱 / 付款页 / 结算页 | 基本对齐 | 当前主要围绕 `type=pay` |
| 已支付台账 | `payment.ledger` | demo 闭环证据 / 结算支撑事实 | 局部使用 | 还未成为所有付款汇总页的唯一来源 |
| 结算完成态 | `sc.settlement.order(state=done)` | 决策引擎 / Flow Map / Completion | 基本对齐 | 已用于完整闭环样板判断 |
| 生命周期 | `project.project.lifecycle_state` | Flow Map / Completion / 状态解释 | 混合口径 | 目前仍作为主线阶段粗粒度入口 |
| 执行里程碑 | `project.project.sc_execution_state` | 驾驶舱状态解释 | 局部使用 | 只用于解释层，不应用来替代业务事实 |

## 已确认的错口径模式

### 1. 金额和条数不同源

已修复的典型问题：

- `Flow Map` 判定成本已到位
- `成本合计` 却显示 `0`
- `成本记录` 仍显示 `0 条`

根因：

- 金额按 `project.cost.ledger`
- 条数或摘要仍按 `account.move`

### 2. 进度和任务完成态不同源

已修复的典型问题：

- 任务其实未完成
- 但进度被 `stage_id.fold` 推成已完成

根因：

- 旧口径把 kanban/stage 当成业务完成态
- 正确口径应是 `project.task.sc_state`

### 3. 状态先行、事实滞后

仍需继续关注的典型问题：

- `Flow Map` 或 `Completion` 先进入后续阶段
- 但上游业务证据还不够厚

根因：

- `lifecycle_state` 是粗粒度状态
- `cost/payment/settlement` 是细粒度事实
- 当前仍存在混合推断

## 当前统一口径

### Task

- 唯一完成态事实：`project.task.sc_state=done`
- 唯一进度口径：`done_count / total_count`

### Cost

- 唯一主事实：`project.cost.ledger`
- `account.move` 仅在没有 ledger 时作为 fallback

### Payment

- 当前主事实：`payment.request(type=pay)`
- `payment.ledger` 作为“已支付证据层”
- 后续若要继续收口，应明确：
  - 驾驶舱展示“付款申请”
  - 还是展示“已支付完成”

### Settlement

- 唯一完成事实：`sc.settlement.order(state=done)`

## 本轮 Guard 范围

本轮新增 `business_fact_consistency_guard`，只验证最容易再次回归的核心口径：

- 驾驶舱 `cost_total` 必须等于成本页 `cost_total_amount`
- 结算页 `total_cost` 必须等于成本页 `cost_total_amount`
- 驾驶舱 `payment_total` 必须等于结算页 `total_payment`
- 成本页 `cost_record_count` 必须等于结算页 `cost_record_count`
- 驾驶舱 `progress_percent` 必须等于决策引擎的任务事实进度

## 下一轮建议

下一轮不该再继续点修单个页面，而应继续做：

### Payment Fact Consistency v1

目标：

- 明确 `payment.request` 与 `payment.ledger` 的职责边界
- 决定驾驶舱和切片展示的是“申请事实”还是“支付事实”
- 让 `payment` 和 `settlement` 也形成像 `cost` 一样的单一口径
