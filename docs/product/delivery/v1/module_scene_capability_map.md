# Module Scene Capability Map V1

- version: v1
- module_count: 9
- delivery_scope_scene_count: 22
- assigned_scope_scene_count: 22
- unassigned_scope_scene_count: 0
- unknown_scene_ref_count: 22
- unknown_capability_ref_count: 42
- error_count: 2
- warning_count: 0

## Acceptance

- module_count_le_10: PASS
- each_module_has_scene: PASS
- scope_scene_unassigned_eq_0: PASS
- unknown_scene_ref_eq_0: FAIL
- unknown_capability_ref_eq_0: FAIL

| module_key | module_name | target_roles | entry_scenes | capabilities |
|---|---|---|---|---|
| project_initiation_ledger | 项目立项与台账 | pm,purchase_manager | projects.intake,projects.ledger,projects.list | project.document.open,project.initiation.enter,project.lifecycle.open,project.list.open,project.structure.manage,workspace.project.watch |
| project_execution_collab | 项目执行与任务协同 | pm | projects.dashboard,projects.execution | project.dashboard.open,project.risk.list,project.task.board,project.task.list,project.weekly_report.open,workspace.today.focus |
| purchase_material_collab | 采购与物资协同 | purchase_manager,pm | cost.project_boq | cost.boq.manage,material.catalog.open,material.procurement.list,project.document.open |
| payment_request_approval | 付款申请与审批 | finance,pm | finance.center,finance.payment_requests | finance.approval.center,finance.exception.monitor,finance.payment_request.form,finance.payment_request.list |
| funding_settlement_ledger | 资金与结算台账 | finance | finance.payment_ledger,finance.settlement_orders,finance.treasury_ledger | finance.invoice.list,finance.ledger.payment,finance.ledger.treasury,finance.plan.funding,finance.settlement.order |
| cost_budget_profit | 成本预算与利润分析 | pm,finance | cost.cost_compare,cost.profit_compare,cost.project_budget,cost.project_cost_ledger,cost.project_progress | cost.budget.manage,cost.ledger.open,cost.profit.compare,cost.progress.report |
| executive_dashboard | 经营指标与领导看板 | executive | finance.operating_metrics,portal.dashboard | analytics.dashboard.executive,analytics.exception.list,analytics.project.focus,finance.metrics.operating |
| lifecycle_governance | 生命周期与治理审计 | admin,executive | portal.capability_matrix,portal.lifecycle | analytics.lifecycle.monitor,contract.settlement.audit,governance.capability.matrix,governance.runtime.audit,governance.scene.openability |
| masterdata_workspace | 主数据与工作台 | pm,finance,purchase_manager,executive | data.dictionary,default | contract.center.open,contract.expense.track,contract.income.track,project.lifecycle.transition |
