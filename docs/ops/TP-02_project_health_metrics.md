# TP-02｜项目健康度指标字典 v1

本表仅使用现有字段，不新增计算逻辑。用于 PM 在项目概览区完成“健康判断”。

## 指标清单（v1）

| 指标名 | 模型.字段 | 计算方式/来源 | 展示区 | PM 密度 | 缺失展示 |
| --- | --- | --- | --- | --- | --- |
| 合同额（已付款合同额） | project.project.pay_contract_total | 已付款合同额汇总（项目级） | 概览区 | 低 | 显示 0 |
| 已结算金额 | project.project.pay_settlement_total | 结算金额汇总（项目级） | 概览区 | 低 | 显示 0 |
| 已付款金额 | project.project.pay_paid_total | 付款金额汇总（项目级） | 概览区 | 低 | 显示 0 |
| 应付未付金额 | project.project.pay_unpaid_total | 已结算未付款差额 | 概览区 | 低 | 显示 0 |
| 成本台账实际 | project.project.cost_ledger_amount_actual | 成本台账汇总（项目级） | 管理支撑区 | 低 | 显示 0 |
| 当前预算成本目标 | project.project.budget_active_cost_target | 当前预算成本目标 | 管理支撑区 | 低 | 显示 0 |
| 成本偏差 | project.project.cost_budget_gap | 预算目标-台账实际（正值=低于预算，负值=超预算） | 管理支撑区 | 低 | 显示 0 |
| 进度完成率 | project.project.progress_rate_latest | 最近进度计量完成率 | 管理支撑区 | 低 | 显示 0（并标记“暂无进度数据”） |
| 资料完备率 | project.project.document_completion_rate | 资料完备率统计 | 协作与系统区 | 低 | 显示 0 |
| 合同数量 | project.project.contract_count | 合同数量汇总（辅助指标） | 管理支撑区 | 低 | 显示 0 |

## 说明

- 本阶段只做“摘要型指标”，不引入明细与 drilldown。
- 若无权限访问数据，指标返回 0（由模型层守卫保证）。
- 后续若要扩展指标，需明确所属分区与 PM 展示密度。
- 本指标字典仅用于项目健康判断，不用于绩效考核或财务核算。
