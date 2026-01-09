# TP-08｜页面表达契约表（v0.1）

> 定义 PM 视角下每个区块允许出现的控件与交互方式。
> 仅约束“表达”，不涉及权限实现细节。

| 区块 | PM 可见 | 展示密度 | 交互 | 依赖字段 | 解释锚点 |
| --- | --- | --- | --- | --- | --- |
| 叙事卡 | 是 | 低 | 只读、不可点 | lifecycle_state, cost_budget_gap, pay_settlement_total, pay_paid_total, progress_rate_latest, progress_entry_count, document_completion_rate, contract_count | TP-04 N-01..N-06 |
| 软提示 | 是 | 低 | 只读、不可点 | cost_budget_gap, pay_settlement_total, pay_paid_total, progress_rate_latest, progress_entry_count, document_completion_rate, contract_count | TP-05 W-01..W-05 |
| BOQ 状态卡 | 是 | 低 | 只读、不可点 | boq_imported, boq_line_count, boq_amount_leaf_total, boq_version_latest | TP-07（BOQ 裁决）/ TP-03（BOQ 降维） |
| WBS 状态卡 | 是 | 低 | 只读、不可点 | wbs_ready, wbs_node_count | TP-07（WBS 裁决） |
| 合同汇总 | 是 | 低 | 只读、不可点 | contract_count, contract_income_total, contract_expense_total | TP-07（合同裁决）/ TP-03（合同降维） |
| 成本/进度汇总 | 是 | 低 | 只读、不可点 | budget_active_cost_target, cost_ledger_amount_actual, cost_budget_gap, progress_rate_latest | TP-07（成本/进度裁决）/ TP-02（指标字典） |
| 工程资料完备度 | 是 | 低 | 只读、不可点 | document_completion_rate, document_required_count, document_missing_count | TP-07（资料裁决）/ TP-02（指标字典） |

## 约束说明

- PM 视角所有区块默认不可点击，不提供 drill-down。
- 字段缺失或无权限时：显示 0/空，不触发跨中心读取。
- 若需要“可点”，必须在本表中声明具体入口与防点炸策略。
