# 项目驾驶舱字段字典 v1（P1）

## Header

- `data.summary.name`：项目名称
- `data.summary.project_code`：项目编码
- `data.summary.partner_name`：建设单位/甲方
- `data.summary.manager_name`：项目经理
- `data.summary.stage_name`：当前阶段
- `data.summary.date_start/date_end`：项目起止日期
- `data.semantic_summary.*`：面向产品表达的头部语义字段

## Metrics

- `data.kpi.contract_amount`：合同金额
- `data.kpi.output_value`：已完成产值
- `data.kpi.progress_rate`：完成率（%）
- `data.kpi.cost_spent`：成本支出
- `data.kpi.profit_estimate`：利润估算
- `data.kpi.payment_received`：回款金额
- `data.kpi.payment_rate`：回款率（%）
- `data.kpi.risk_open_count`：未闭环风险数

## Progress

- `data.task_total/task_done/task_overdue`：任务总量/完成/延期
- `data.completion_percent`：任务完成率（%）
- `data.milestone_total/milestone_done/milestone_delay`：里程碑统计
- `data.milestone_progress`：里程碑完成率（%）

## Contract

- `data.summary.contract_total`：合同总额
- `data.summary.executed_amount`：执行金额
- `data.summary.change_amount`：变更金额
- `data.summary.performance_rate`：履约率（%）

## Cost

- `data.summary.budget_target`：目标成本
- `data.summary.actual_cost`：实际成本
- `data.summary.cost_variance`：成本偏差（实际-目标）
- `data.summary.cost_variance_rate`：偏差率（%）

## Finance

- `data.summary.receivable`：应收
- `data.summary.received`：已收
- `data.summary.payable`：应付
- `data.summary.paid`：已付
- `data.summary.gap`：资金缺口

## Risk

- `data.summary.risk_total`：风险总数
- `data.summary.risk_open`：未关闭风险数
- `data.summary.risk_critical`：高风险数
- `data.summary.risk_score`：风险评分（0-100）
- `data.summary.risk_level`：风险等级（low/medium/high）

