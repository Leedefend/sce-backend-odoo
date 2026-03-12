# Project Cockpit Field Dictionary v1 (P1)

## Header

- `data.summary.name`: project name
- `data.summary.project_code`: project code
- `data.summary.partner_name`: owner/client
- `data.summary.manager_name`: project manager
- `data.summary.stage_name`: current stage
- `data.summary.date_start/date_end`: project timeline
- `data.semantic_summary.*`: product-facing semantic header fields

## Metrics

- `data.kpi.contract_amount`: contract amount
- `data.kpi.output_value`: output delivered
- `data.kpi.progress_rate`: completion rate (%)
- `data.kpi.cost_spent`: cost spent
- `data.kpi.profit_estimate`: estimated profit
- `data.kpi.payment_received`: cash received
- `data.kpi.payment_rate`: collection rate (%)
- `data.kpi.risk_open_count`: open risks

## Progress

- `data.task_total/task_done/task_overdue`: tasks total/done/overdue
- `data.completion_percent`: task completion rate (%)
- `data.milestone_total/milestone_done/milestone_delay`: milestone counts
- `data.milestone_progress`: milestone completion rate (%)

## Contract

- `data.summary.contract_total`: total contract amount
- `data.summary.executed_amount`: executed amount
- `data.summary.change_amount`: change amount
- `data.summary.performance_rate`: performance rate (%)

## Cost

- `data.summary.budget_target`: budget target
- `data.summary.actual_cost`: actual cost
- `data.summary.cost_variance`: variance (actual - budget)
- `data.summary.cost_variance_rate`: variance rate (%)

## Finance

- `data.summary.receivable`: receivable
- `data.summary.received`: received
- `data.summary.payable`: payable
- `data.summary.paid`: paid
- `data.summary.gap`: cash gap

## Risk

- `data.summary.risk_total`: total risks
- `data.summary.risk_open`: open risks
- `data.summary.risk_critical`: high risks
- `data.summary.risk_score`: risk score (0-100)
- `data.summary.risk_level`: risk level (low/medium/high)

