# TP-07｜PM 最终可见面裁决表（空白模板）

| 区块/入口 | 当前表现 | 裁决（保留/降维/移除） | 表达密度 | 保留字段 | 隐藏字段 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| 项目概览 · 关键指标卡 | 多指标并列，直接展示金额 | 保留 | 低 | pay_contract_total / pay_paid_total / pay_settlement_total / pay_unpaid_total | 所有明细类字段与 drill-down 行为（列表、分析视图、跳转 action） | 仅展示状态级金额，不提供明细入口 |
| 合同汇总区块 | 合同页签含明细列表与配置入口 | 保留 | 低 | contract_count / contract_income_total / contract_expense_total | 新建、配置、审批、合同明细列表与所有 drill-down 行为（列表、表单、分析视图、跳转 action） | 仅做合同规模与状态摘要，不进入合同明细 |
| BOQ / 工程量清单 | BOQ 页签含明细列表与导入动作 | 降维 | 低 | BOQ 是否已导入 / BOQ 总金额 / BOQ 版本 | BOQ 明细列表、导入、结构维护、分析视图与所有 drill-down 行为 | 只展示状态卡与汇总，不进入 BOQ 明细；状态仅用于“是否具备执行基础”的判断信号 |
| 成本 / 进度汇总区块 | 管理支撑区显示预算目标、实际、偏差与进度 | 保留 | 低 | budget_active_cost_target / cost_ledger_amount_actual / cost_budget_gap / progress_rate_latest | 明细台账、进度明细、趋势分析、任何 drill-down 行为 | 仅展示状态级结果，不展示趋势/历史对比/阶段分析，仅作为“当前是否偏离预期”的判断信号 |
| 工程资料 / 文档完备度区块 | 工程资料页签含明细列表 | 保留 | 低 | document_completion_rate / document_required_count / document_missing_count | 文档明细列表与所有 drill-down 行为 | 仅展示完备度与缺失数量，作为提醒信号，不进入资料明细；不作为责任归属或合规判断依据 |
