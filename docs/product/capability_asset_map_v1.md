# Capability Asset Map v1

- source: capability_registry + release_capability_report + scene_capability_matrix_report
- capability_count: 63
- active_used_count: 63
- structural_only_count: 0
- isolated_count: 0
- unresolved_intent_count: 0
- missing_capability_ref_count: 0
- error_count: 0
- warning_count: 0

## Acceptance

- zero_unresolved_intent: PASS
- zero_missing_capability_ref: PASS
- zero_structural_only: PASS

## Capability -> Scene -> Role -> Intent

| capability | scene_entry | scene_refs | runtime_ready_roles | intent | usage_status |
|---|---|---|---|---|---|
| analytics.dashboard.executive | - | finance.operating_metrics,portal.dashboard | - | ui.contract | active_used |
| analytics.exception.list | - | finance.operating_metrics,portal.dashboard | - | ui.contract | active_used |
| analytics.lifecycle.monitor | - | portal.capability_matrix,portal.lifecycle | - | ui.contract | active_used |
| analytics.project.focus | - | finance.operating_metrics,portal.dashboard | - | ui.contract | active_used |
| construction.diary.open | - | construction.diary,construction.execution,construction.plan,construction.plan_report,quality.center,quality.recheck,quality.rectification,safety.center,safety.recheck,safety.rectification | - | ui.contract | active_used |
| construction.plan.manage | - | construction.diary,construction.execution,construction.plan,construction.plan_report,quality.center,quality.recheck,quality.rectification,safety.center,safety.recheck,safety.rectification | - | ui.contract | active_used |
| construction.plan.report | - | construction.diary,construction.execution,construction.plan,construction.plan_report,quality.center,quality.recheck,quality.rectification,safety.center,safety.recheck,safety.rectification | - | ui.contract | active_used |
| contract.center.open | - | contract.center,contracts.workspace,data.dictionary,my_work.workspace,workspace.home | - | ui.contract | active_used |
| contract.expense.track | - | contract.center,contracts.workspace,data.dictionary,my_work.workspace,workspace.home | - | ui.contract | active_used |
| contract.income.track | - | contract.center,contracts.workspace,data.dictionary,my_work.workspace,workspace.home | - | ui.contract | active_used |
| contract.settlement.audit | - | portal.capability_matrix,portal.lifecycle | - | ui.contract | active_used |
| cost.boq.manage | - | cost.project_boq,equipment.management,equipment.request,equipment.settlement,equipment.usage,labor.attendance,labor.management,labor.request,labor.settlement,material.acceptance,material.catalog,material.center,material.inbound,material.outbound,material.price_library,material.procurement,material.rental,material.rental_order,material.rental_settlement,material.rfq,material.settlement,subcontract.management,subcontract.register,subcontract.request,subcontract.settlement | - | ui.contract | active_used |
| cost.budget.manage | - | cost.analysis,cost.budget_alloc,cost.cost_compare,cost.profit_compare,cost.project_budget,cost.project_cost_ledger,cost.project_progress | - | ui.contract | active_used |
| cost.ledger.open | - | cost.analysis,cost.budget_alloc,cost.cost_compare,cost.profit_compare,cost.project_budget,cost.project_cost_ledger,cost.project_progress | - | ui.contract | active_used |
| cost.profit.compare | - | cost.analysis,cost.budget_alloc,cost.cost_compare,cost.profit_compare,cost.project_budget,cost.project_cost_ledger,cost.project_progress | - | ui.contract | active_used |
| cost.progress.report | - | cost.analysis,cost.budget_alloc,cost.cost_compare,cost.profit_compare,cost.project_budget,cost.project_cost_ledger,cost.project_progress | - | ui.contract | active_used |
| equipment.plan.manage | - | cost.project_boq,equipment.management,equipment.request,equipment.settlement,equipment.usage,labor.attendance,labor.management,labor.request,labor.settlement,material.acceptance,material.catalog,material.center,material.inbound,material.outbound,material.price_library,material.procurement,material.rental,material.rental_order,material.rental_settlement,material.rfq,material.settlement,subcontract.management,subcontract.register,subcontract.request,subcontract.settlement | - | ui.contract | active_used |
| equipment.request.list | - | cost.project_boq,equipment.management,equipment.request,equipment.settlement,equipment.usage,labor.attendance,labor.management,labor.request,labor.settlement,material.acceptance,material.catalog,material.center,material.inbound,material.outbound,material.price_library,material.procurement,material.rental,material.rental_order,material.rental_settlement,material.rfq,material.settlement,subcontract.management,subcontract.register,subcontract.request,subcontract.settlement | - | ui.contract | active_used |
| equipment.settlement.list | - | cost.project_boq,equipment.management,equipment.request,equipment.settlement,equipment.usage,labor.attendance,labor.management,labor.request,labor.settlement,material.acceptance,material.catalog,material.center,material.inbound,material.outbound,material.price_library,material.procurement,material.rental,material.rental_order,material.rental_settlement,material.rfq,material.settlement,subcontract.management,subcontract.register,subcontract.request,subcontract.settlement | - | ui.contract | active_used |
| equipment.usage.list | - | cost.project_boq,equipment.management,equipment.request,equipment.settlement,equipment.usage,labor.attendance,labor.management,labor.request,labor.settlement,material.acceptance,material.catalog,material.center,material.inbound,material.outbound,material.price_library,material.procurement,material.rental,material.rental_order,material.rental_settlement,material.rfq,material.settlement,subcontract.management,subcontract.register,subcontract.request,subcontract.settlement | - | ui.contract | active_used |
| finance.approval.center | - | finance.center,finance.payment_requests,finance.workspace | - | ui.contract | active_used |
| finance.exception.monitor | - | finance.center,finance.payment_requests,finance.workspace | - | ui.contract | active_used |
| finance.invoice.list | - | finance.payment_ledger,finance.settlement_orders,finance.treasury_ledger | - | ui.contract | active_used |
| finance.ledger.payment | - | finance.payment_ledger,finance.settlement_orders,finance.treasury_ledger | - | ui.contract | active_used |
| finance.ledger.treasury | - | finance.payment_ledger,finance.settlement_orders,finance.treasury_ledger | - | ui.contract | active_used |
| finance.metrics.operating | - | finance.operating_metrics,portal.dashboard | - | ui.contract | active_used |
| finance.payment_request.form | - | finance.center,finance.payment_requests,finance.workspace | - | ui.contract | active_used |
| finance.payment_request.list | - | finance.center,finance.payment_requests,finance.workspace | - | ui.contract | active_used |
| finance.plan.funding | - | finance.payment_ledger,finance.settlement_orders,finance.treasury_ledger | - | ui.contract | active_used |
| finance.settlement.order | - | finance.payment_ledger,finance.settlement_orders,finance.treasury_ledger | - | ui.contract | active_used |
| governance.capability.matrix | - | portal.capability_matrix,portal.lifecycle | - | ui.contract | active_used |
| governance.runtime.audit | - | portal.capability_matrix,portal.lifecycle | - | ui.contract | active_used |
| governance.scene.openability | - | portal.capability_matrix,portal.lifecycle | - | ui.contract | active_used |
| labor.attendance.list | - | cost.project_boq,equipment.management,equipment.request,equipment.settlement,equipment.usage,labor.attendance,labor.management,labor.request,labor.settlement,material.acceptance,material.catalog,material.center,material.inbound,material.outbound,material.price_library,material.procurement,material.rental,material.rental_order,material.rental_settlement,material.rfq,material.settlement,subcontract.management,subcontract.register,subcontract.request,subcontract.settlement | - | ui.contract | active_used |
| labor.plan.manage | - | cost.project_boq,equipment.management,equipment.request,equipment.settlement,equipment.usage,labor.attendance,labor.management,labor.request,labor.settlement,material.acceptance,material.catalog,material.center,material.inbound,material.outbound,material.price_library,material.procurement,material.rental,material.rental_order,material.rental_settlement,material.rfq,material.settlement,subcontract.management,subcontract.register,subcontract.request,subcontract.settlement | - | ui.contract | active_used |
| labor.request.list | - | cost.project_boq,equipment.management,equipment.request,equipment.settlement,equipment.usage,labor.attendance,labor.management,labor.request,labor.settlement,material.acceptance,material.catalog,material.center,material.inbound,material.outbound,material.price_library,material.procurement,material.rental,material.rental_order,material.rental_settlement,material.rfq,material.settlement,subcontract.management,subcontract.register,subcontract.request,subcontract.settlement | - | ui.contract | active_used |
| labor.settlement.list | - | cost.project_boq,equipment.management,equipment.request,equipment.settlement,equipment.usage,labor.attendance,labor.management,labor.request,labor.settlement,material.acceptance,material.catalog,material.center,material.inbound,material.outbound,material.price_library,material.procurement,material.rental,material.rental_order,material.rental_settlement,material.rfq,material.settlement,subcontract.management,subcontract.register,subcontract.request,subcontract.settlement | - | ui.contract | active_used |
| material.catalog.open | - | cost.project_boq,equipment.management,equipment.request,equipment.settlement,equipment.usage,labor.attendance,labor.management,labor.request,labor.settlement,material.acceptance,material.catalog,material.center,material.inbound,material.outbound,material.price_library,material.procurement,material.rental,material.rental_order,material.rental_settlement,material.rfq,material.settlement,subcontract.management,subcontract.register,subcontract.request,subcontract.settlement | - | ui.contract | active_used |
| material.procurement.list | - | cost.project_boq,equipment.management,equipment.request,equipment.settlement,equipment.usage,labor.attendance,labor.management,labor.request,labor.settlement,material.acceptance,material.catalog,material.center,material.inbound,material.outbound,material.price_library,material.procurement,material.rental,material.rental_order,material.rental_settlement,material.rfq,material.settlement,subcontract.management,subcontract.register,subcontract.request,subcontract.settlement | - | ui.contract | active_used |
| project.board.open | - | project.management,projects.dashboard,projects.execution,risk.center,risk.monitor,task.center | - | ui.contract | active_used |
| project.dashboard.enter | - | project.management,projects.dashboard,projects.execution,risk.center,risk.monitor,task.center | - | ui.contract | active_used |
| project.dashboard.open | - | project.management,projects.dashboard,projects.execution,risk.center,risk.monitor,task.center | - | ui.contract | active_used |
| project.document.open | - | cost.project_boq,equipment.management,equipment.request,equipment.settlement,equipment.usage,labor.attendance,labor.management,labor.request,labor.settlement,material.acceptance,material.catalog,material.center,material.inbound,material.outbound,material.price_library,material.procurement,material.rental,material.rental_order,material.rental_settlement,material.rfq,material.settlement,projects.intake,projects.ledger,projects.list,subcontract.management,subcontract.register,subcontract.request,subcontract.settlement | - | ui.contract | active_used |
| project.execution.advance | - | project.management,projects.dashboard,projects.execution,risk.center,risk.monitor,task.center | - | ui.contract | active_used |
| project.execution.enter | - | project.management,projects.dashboard,projects.execution,risk.center,risk.monitor,task.center | - | ui.contract | active_used |
| project.initiation.enter | - | projects.intake,projects.ledger,projects.list | - | ui.contract | active_used |
| project.lifecycle.open | - | projects.intake,projects.ledger,projects.list | - | ui.contract | active_used |
| project.lifecycle.transition | - | contract.center,contracts.workspace,data.dictionary,my_work.workspace,workspace.home | - | ui.contract | active_used |
| project.list.open | - | projects.intake,projects.ledger,projects.list | - | ui.contract | active_used |
| project.plan_bootstrap.enter | - | project.management,projects.dashboard,projects.execution,risk.center,risk.monitor,task.center | - | ui.contract | active_used |
| project.risk.list | - | project.management,projects.dashboard,projects.execution,risk.center,risk.monitor,task.center | - | ui.contract | active_used |
| project.structure.manage | - | projects.intake,projects.ledger,projects.list | - | ui.contract | active_used |
| project.task.board | - | project.management,projects.dashboard,projects.execution,risk.center,risk.monitor,task.center | - | ui.contract | active_used |
| project.task.list | - | project.management,projects.dashboard,projects.execution,risk.center,risk.monitor,task.center | - | ui.contract | active_used |
| project.weekly_report.open | - | project.management,projects.dashboard,projects.execution,risk.center,risk.monitor,task.center | - | ui.contract | active_used |
| quality.issue.list | - | construction.diary,construction.execution,construction.plan,construction.plan_report,quality.center,quality.recheck,quality.rectification,safety.center,safety.recheck,safety.rectification | - | ui.contract | active_used |
| quality.recheck.list | - | construction.diary,construction.execution,construction.plan,construction.plan_report,quality.center,quality.recheck,quality.rectification,safety.center,safety.recheck,safety.rectification | - | ui.contract | active_used |
| quality.rectification.list | - | construction.diary,construction.execution,construction.plan,construction.plan_report,quality.center,quality.recheck,quality.rectification,safety.center,safety.recheck,safety.rectification | - | ui.contract | active_used |
| safety.issue.list | - | construction.diary,construction.execution,construction.plan,construction.plan_report,quality.center,quality.recheck,quality.rectification,safety.center,safety.recheck,safety.rectification | - | ui.contract | active_used |
| safety.recheck.list | - | construction.diary,construction.execution,construction.plan,construction.plan_report,quality.center,quality.recheck,quality.rectification,safety.center,safety.recheck,safety.rectification | - | ui.contract | active_used |
| safety.rectification.list | - | construction.diary,construction.execution,construction.plan,construction.plan_report,quality.center,quality.recheck,quality.rectification,safety.center,safety.recheck,safety.rectification | - | ui.contract | active_used |
| workspace.project.watch | - | projects.intake,projects.ledger,projects.list | - | ui.contract | active_used |
| workspace.today.focus | - | project.management,projects.dashboard,projects.execution,risk.center,risk.monitor,task.center | - | ui.contract | active_used |

## Isolated Capabilities

- none
