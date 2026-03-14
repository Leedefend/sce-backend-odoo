# project.management 驾驶舱指标口径与数据来源矩阵（v1）

## 1. 目标与边界

- 本文档用于冻结 `project.management.dashboard` 的汇总指标业务口径。
- 指标必须可追溯到业务对象，禁止使用技术字段或非业务口径“凑数”。
- 前端只做语义展示与格式化，不参与业务重算。

## 2. 通用原则

- 业务优先：优先使用业务主数据与业务事件汇总。
- 可追溯：每个指标都要有明确来源模型与字段。
- 可降级：业务数据缺失时允许降级，但必须保持业务语义，不伪造经营值。
- 可解释：空态必须明确告知缺失的是哪类业务数据。

## 3. 指标口径矩阵

| 指标键 | 展示名称 | 业务口径 | 来源模型 | 来源字段 | 允许降级 |
| --- | --- | --- | --- | --- | --- |
| `contract_total` | 收入合同总额 | 当前项目 `type=out` 合同金额汇总 | `construction.contract` | `amount_total/amount` | 否 |
| `subcontract_total` | 支出合同总额 | 当前项目 `type=in` 合同金额汇总 | `construction.contract` | `amount_total/amount` | 否 |
| `executed_amount` | 执行金额 | 当前项目收入合同中执行态金额汇总 | `construction.contract` | `amount_total/amount + state` | 否 |
| `performance_rate` | 履约率 | `executed_amount / contract_total` | 推导 | 汇总计算 | 否 |
| `output_value` | 已完成产值 | 业务填报值优先，否则 `contract_total * progress_rate` | `project.project` + `construction.contract` | `output_value_*` / `contract_total` / `progress_rate` | 是（按进度推导） |
| `budget_target` | 目标成本 | 当前项目预算目标 | `project.project` | `budget_total` / `budget_active_cost_target` | 否 |
| `actual_cost` | 实际成本 | 当前项目成本台账累计 | `project.cost.ledger` | `amount/actual_amount` | 否 |
| `cost_variance` | 成本偏差 | `actual_cost - budget_target` | 推导 | 汇总计算 | 否 |
| `cost_completion_rate` | 成本完成率 | `actual_cost / budget_target` | 推导 | 汇总计算 | 否 |
| `receivable` | 应收 | 当前项目收入合同总额 | `construction.contract` | `type=out + amount_total/amount` | 否 |
| `payable` | 应付 | 当前项目支出合同总额 | `construction.contract` | `type=in + amount_total/amount` | 否 |
| `received` | 已收 | 当前项目收款申请已完成金额 | `payment.request` | `type=receive + state + amount` | 否 |
| `paid` | 已付 | 当前项目付款申请已完成金额 | `payment.request` | `type=pay + state + amount` | 否 |
| `receive_pending` | 待收 | 当前项目收款申请待处理金额 | `payment.request` | `type=receive + state + amount` | 否 |
| `pay_pending` | 待付 | 当前项目付款申请待处理金额 | `payment.request` | `type=pay + state + amount` | 否 |
| `gap` | 资金缺口 | `receivable - received` | 推导 | 汇总计算 | 否 |
| `net_cash` | 净现金流 | `received - paid` | 推导 | 汇总计算 | 否 |

## 3.1 进度口径矩阵（project.progress）

| 指标键 | 展示名称 | 业务口径 | 来源模型 | 来源字段 | 允许降级 |
| --- | --- | --- | --- | --- | --- |
| `task_total` | 任务总数 | 当前项目任务总量 | `project.task` | 计数 | 否 |
| `task_done` | 已完成任务 | `kanban_state=done` 的任务数 | `project.task` | `kanban_state` | 否 |
| `task_open` | 未完成任务 | `task_total - task_done` | 推导 | 汇总计算 | 否 |
| `task_critical` | 关键任务 | 高优先级任务数 | `project.task` | `priority` | 否 |
| `task_blocked` | 阻塞任务 | `kanban_state=blocked` 的任务数 | `project.task` | `kanban_state` | 否 |
| `task_overdue` | 延期任务 | 截止日期早于今天的任务数 | `project.task` | `date_deadline` | 否 |
| `completion_percent` | 总体完成率 | `task_done / task_total` | 推导 | 汇总计算 | 否 |
| `milestone_total` | 里程碑总数 | 当前项目里程碑总量 | `project.milestone` | 计数 | 否 |
| `milestone_done` | 已完成里程碑 | 完成态里程碑数 | `project.milestone` | `status` | 否 |
| `milestone_delay` | 延期里程碑 | 延期/阻塞态里程碑数 | `project.milestone` | `status` | 否 |
| `milestone_progress` | 里程碑完成率 | `milestone_done / milestone_total` | 推导 | 汇总计算 | 否 |
| `milestone_upcoming_days` | 下一里程碑剩余天数 | 最近未完成里程碑计划日期减今天 | `project.milestone` | `plan_date` | 是（无里程碑返回0） |
| `critical_path_health` | 关键路径健康度 | 按阻塞任务与延期任务阈值分级 | 推导 | 规则计算 | 否 |

## 3.2 风险-进度联动口径（project.risk）

| 指标键 | 展示名称 | 业务口径 | 来源模型 | 来源字段 | 允许降级 |
| --- | --- | --- | --- | --- | --- |
| `progress_task_overdue` | 任务延期风险计数 | 项目逾期任务数 | `project.task` | `date_deadline` | 否 |
| `progress_task_blocked` | 任务阻塞风险计数 | 项目阻塞任务数 | `project.task` | `kanban_state` | 否 |
| `progress_milestone_delay` | 里程碑延期风险计数 | 项目延期里程碑数 | `project.milestone` | `status` | 否 |
| `risk_score` | 风险评分 | 综合风险+进度联动信号评分 | 推导 | 规则计算 | 否 |
| `risk_level` | 风险等级 | 按评分阈值分级 | 推导 | 规则计算 | 否 |

## 3.3 驾驶舱动作优先级口径（header.quick_actions）

- 动作必须按“待处理数量优先 + 业务优先级”排序。
- 允许动作（v1）：
  - `open_task_overdue`
  - `open_task_blocked`
  - `open_risk_list`
  - `open_payment_requests`
  - `open_project_form`（导航兜底）
- 禁止在前端重排动作优先级并覆盖后端排序。

## 4. 明确禁止项

- 禁止以 `dashboard_invoice_amount` 替代合同额口径。
- 禁止用付款或开票金额反推产值作为主口径。
- 禁止前端在页面上重算经营指标并覆盖后端结果。
- 禁止把无业务来源的演示常量写入驾驶舱汇总字段。

## 5. 演示数据补齐要求

- 补齐必须落到可重复的 demo 种子（XML/seed hook），禁止仅在会话中手工写库。
- 合同额类指标必须通过 `construction.contract` + `construction.contract.line` 生成。
- 成本类指标必须通过 `project.cost.ledger` 生成。
- 资金类指标必须通过 `payment.request`（含状态）生成。

## 6. 验证要求

- `make verify.project.dashboard.contract` 必须通过。
- `make verify.demo.release.seed DB_NAME=sc_demo` 必须通过。
- 本文档中的关键口径必须由守卫脚本覆盖，防止回退到伪业务聚合。
