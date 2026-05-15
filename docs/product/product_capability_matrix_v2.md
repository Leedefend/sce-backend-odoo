# Product Capability Matrix v2

- target: 63 capability -> 20 product capability -> 10 industry module
- capability_count: 63
- mapped_capability_count: 63
- product_capability_count: 20
- industry_module_count: 10
- unassigned_capability_count: 0
- error_count: 0

## Product Capability List

- product.analytics.executive (executive_dashboard,lifecycle_governance)
- product.contract.center (masterdata_workspace)
- product.cost.control (cost_budget_profit,purchase_material_collab)
- product.execution.collaboration (project_execution_collab,project_initiation_ledger)
- product.finance.approval (payment_request_approval)
- product.finance.ledger (funding_settlement_ledger)
- product.finance.operating_metrics (cost_budget_profit,executive_dashboard)
- product.finance.payment (funding_settlement_ledger,payment_request_approval)
- product.finance.settlement (funding_settlement_ledger,lifecycle_governance)
- product.governance.runtime (lifecycle_governance)
- product.procurement.material (purchase_material_collab)
- product.project.delivery (masterdata_workspace,project_execution_collab,project_initiation_ledger)
- product.project.initiation (project_initiation_ledger)
- product.quality_safety (site_execution_quality_safety)
- product.reporting.weekly (project_execution_collab)
- product.resource.equipment (purchase_material_collab)
- product.resource.labor (purchase_material_collab)
- product.risk.control (payment_request_approval,project_execution_collab)
- product.site.execution (site_execution_quality_safety)
- product.workspace.navigation (project_execution_collab,project_initiation_ledger)

## Capability Mapping

| capability_key | product_capability | industry_module |
|---|---|---|
| analytics.dashboard.executive | product.analytics.executive | executive_dashboard |
| analytics.exception.list | product.analytics.executive | executive_dashboard |
| analytics.lifecycle.monitor | product.analytics.executive | lifecycle_governance |
| analytics.project.focus | product.analytics.executive | executive_dashboard |
| construction.diary.open | product.site.execution | site_execution_quality_safety |
| construction.plan.manage | product.site.execution | site_execution_quality_safety |
| construction.plan.report | product.site.execution | site_execution_quality_safety |
| contract.center.open | product.contract.center | masterdata_workspace |
| contract.expense.track | product.contract.center | masterdata_workspace |
| contract.income.track | product.contract.center | masterdata_workspace |
| contract.settlement.audit | product.finance.settlement | lifecycle_governance |
| cost.boq.manage | product.cost.control | purchase_material_collab |
| cost.budget.manage | product.cost.control | cost_budget_profit |
| cost.ledger.open | product.cost.control | cost_budget_profit |
| cost.profit.compare | product.finance.operating_metrics | cost_budget_profit |
| cost.progress.report | product.cost.control | cost_budget_profit |
| equipment.plan.manage | product.resource.equipment | purchase_material_collab |
| equipment.request.list | product.resource.equipment | purchase_material_collab |
| equipment.settlement.list | product.resource.equipment | purchase_material_collab |
| equipment.usage.list | product.resource.equipment | purchase_material_collab |
| finance.approval.center | product.finance.approval | payment_request_approval |
| finance.exception.monitor | product.risk.control | payment_request_approval |
| finance.invoice.list | product.finance.ledger | funding_settlement_ledger |
| finance.ledger.payment | product.finance.ledger | funding_settlement_ledger |
| finance.ledger.treasury | product.finance.ledger | funding_settlement_ledger |
| finance.metrics.operating | product.finance.operating_metrics | executive_dashboard |
| finance.payment_request.form | product.finance.payment | payment_request_approval |
| finance.payment_request.list | product.finance.payment | payment_request_approval |
| finance.plan.funding | product.finance.payment | funding_settlement_ledger |
| finance.settlement.order | product.finance.settlement | funding_settlement_ledger |
| governance.capability.matrix | product.governance.runtime | lifecycle_governance |
| governance.runtime.audit | product.governance.runtime | lifecycle_governance |
| governance.scene.openability | product.governance.runtime | lifecycle_governance |
| labor.attendance.list | product.resource.labor | purchase_material_collab |
| labor.plan.manage | product.resource.labor | purchase_material_collab |
| labor.request.list | product.resource.labor | purchase_material_collab |
| labor.settlement.list | product.resource.labor | purchase_material_collab |
| material.catalog.open | product.procurement.material | purchase_material_collab |
| material.procurement.list | product.procurement.material | purchase_material_collab |
| project.board.open | product.project.delivery | project_execution_collab |
| project.dashboard.enter | product.project.delivery | project_execution_collab |
| project.dashboard.open | product.project.delivery | project_execution_collab |
| project.document.open | product.execution.collaboration | project_initiation_ledger |
| project.execution.advance | product.execution.collaboration | project_execution_collab |
| project.execution.enter | product.execution.collaboration | project_execution_collab |
| project.initiation.enter | product.project.initiation | project_initiation_ledger |
| project.lifecycle.open | product.project.delivery | project_initiation_ledger |
| project.lifecycle.transition | product.project.delivery | masterdata_workspace |
| project.list.open | product.project.delivery | project_initiation_ledger |
| project.plan_bootstrap.enter | product.project.delivery | project_execution_collab |
| project.risk.list | product.risk.control | project_execution_collab |
| project.structure.manage | product.execution.collaboration | project_initiation_ledger |
| project.task.board | product.execution.collaboration | project_execution_collab |
| project.task.list | product.execution.collaboration | project_execution_collab |
| project.weekly_report.open | product.reporting.weekly | project_execution_collab |
| quality.issue.list | product.quality_safety | site_execution_quality_safety |
| quality.recheck.list | product.quality_safety | site_execution_quality_safety |
| quality.rectification.list | product.quality_safety | site_execution_quality_safety |
| safety.issue.list | product.quality_safety | site_execution_quality_safety |
| safety.recheck.list | product.quality_safety | site_execution_quality_safety |
| safety.rectification.list | product.quality_safety | site_execution_quality_safety |
| workspace.project.watch | product.workspace.navigation | project_initiation_ledger |
| workspace.today.focus | product.workspace.navigation | project_execution_collab |

## Unassigned

- none
