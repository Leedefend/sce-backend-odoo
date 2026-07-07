# Product Delivery Module Capability Smoke

- module_count: 10
- pass_count: 10
- failed_count: 0
- runtime_ready_count: 0
- runtime_pending_count: 10
- error_count: 0

| module | status | runtime_status | runtime_missing_scenes |
|---|---|---|---|
| 项目立项与台账 (project_initiation_ledger) | PASS | PENDING_RUNTIME_SCENE | projects.intake,projects.list,projects.ledger |
| 项目执行与任务协同 (project_execution_collab) | PASS | PENDING_RUNTIME_SCENE | project.management,projects.dashboard,projects.execution,task.center,risk.center,risk.monitor |
| 采购与物资协同 (purchase_material_collab) | PASS | PENDING_RUNTIME_SCENE | cost.project_boq,equipment.management,equipment.request,equipment.settlement,equipment.usage,labor.attendance,labor.management,labor.request,labor.settlement,material.acceptance,material.catalog,material.center,material.inbound,material.outbound,material.price_library,material.procurement,material.rental,material.rental_order,material.rental_settlement,material.rfq,material.settlement,subcontract.management,subcontract.register,subcontract.request,subcontract.settlement |
| 现场执行与质量安全 (site_execution_quality_safety) | PASS | PENDING_RUNTIME_SCENE | construction.execution,construction.plan,construction.plan_report,construction.diary,quality.center,quality.rectification,quality.recheck,safety.center,safety.rectification,safety.recheck |
| 付款申请与审批 (payment_request_approval) | PASS | PENDING_RUNTIME_SCENE | finance.payment_requests,finance.center,finance.workspace |
| 资金与结算台账 (funding_settlement_ledger) | PASS | PENDING_RUNTIME_SCENE | finance.payment_ledger,finance.treasury_ledger,finance.settlement_orders |
| 成本预算与利润分析 (cost_budget_profit) | PASS | PENDING_RUNTIME_SCENE | cost.analysis,cost.budget_alloc,cost.project_budget,cost.project_cost_ledger,cost.cost_compare,cost.profit_compare,cost.project_progress |
| 经营指标与领导看板 (executive_dashboard) | PASS | PENDING_RUNTIME_SCENE | finance.operating_metrics,portal.dashboard |
| 生命周期与治理审计 (lifecycle_governance) | PASS | PENDING_RUNTIME_SCENE | portal.lifecycle,portal.capability_matrix |
| 主数据与工作台 (masterdata_workspace) | PASS | PENDING_RUNTIME_SCENE | workspace.home,my_work.workspace,data.dictionary,contract.center,contracts.workspace |
