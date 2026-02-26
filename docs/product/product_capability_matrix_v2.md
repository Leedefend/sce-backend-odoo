# Product Capability Matrix v2

- target: 42 capability -> 16 product capability -> 8 industry module
- capability_count: 42
- mapped_capability_count: 42
- product_capability_count: 16
- industry_module_count: 8
- unassigned_capability_count: 0
- error_count: 0

## Product Capability List

- product.analytics.executive (module.business_analytics)
- product.contract.center (module.contract_commercial)
- product.cost.control (module.execution_delivery)
- product.execution.collaboration (module.execution_delivery)
- product.finance.approval (module.finance_settlement)
- product.finance.ledger (module.finance_settlement)
- product.finance.operating_metrics (module.business_analytics)
- product.finance.payment (module.finance_settlement)
- product.finance.settlement (module.finance_settlement)
- product.governance.runtime (module.governance_platform)
- product.procurement.material (module.procurement_supply)
- product.project.delivery (module.project_lifecycle)
- product.project.initiation (module.project_lifecycle)
- product.reporting.weekly (module.business_analytics)
- product.risk.control (module.risk_compliance)
- product.workspace.navigation (module.governance_platform)

## Capability Mapping

| capability_key | product_capability | industry_module |
|---|---|---|
| analytics.dashboard.executive | product.analytics.executive | module.business_analytics |
| analytics.exception.list | product.analytics.executive | module.business_analytics |
| analytics.lifecycle.monitor | product.analytics.executive | module.business_analytics |
| analytics.project.focus | product.analytics.executive | module.business_analytics |
| contract.center.open | product.contract.center | module.contract_commercial |
| contract.expense.track | product.contract.center | module.contract_commercial |
| contract.income.track | product.contract.center | module.contract_commercial |
| contract.settlement.audit | product.finance.settlement | module.finance_settlement |
| cost.boq.manage | product.cost.control | module.execution_delivery |
| cost.budget.manage | product.cost.control | module.execution_delivery |
| cost.ledger.open | product.cost.control | module.execution_delivery |
| cost.profit.compare | product.finance.operating_metrics | module.business_analytics |
| cost.progress.report | product.cost.control | module.execution_delivery |
| finance.approval.center | product.finance.approval | module.finance_settlement |
| finance.exception.monitor | product.risk.control | module.risk_compliance |
| finance.invoice.list | product.finance.ledger | module.finance_settlement |
| finance.ledger.payment | product.finance.ledger | module.finance_settlement |
| finance.ledger.treasury | product.finance.ledger | module.finance_settlement |
| finance.metrics.operating | product.finance.operating_metrics | module.business_analytics |
| finance.payment_request.form | product.finance.payment | module.finance_settlement |
| finance.payment_request.list | product.finance.payment | module.finance_settlement |
| finance.plan.funding | product.finance.payment | module.finance_settlement |
| finance.settlement.order | product.finance.settlement | module.finance_settlement |
| governance.capability.matrix | product.governance.runtime | module.governance_platform |
| governance.runtime.audit | product.governance.runtime | module.governance_platform |
| governance.scene.openability | product.governance.runtime | module.governance_platform |
| material.catalog.open | product.procurement.material | module.procurement_supply |
| material.procurement.list | product.procurement.material | module.procurement_supply |
| project.board.open | product.project.delivery | module.project_lifecycle |
| project.dashboard.open | product.project.delivery | module.project_lifecycle |
| project.document.open | product.execution.collaboration | module.execution_delivery |
| project.initiation.enter | product.project.initiation | module.project_lifecycle |
| project.lifecycle.open | product.project.delivery | module.project_lifecycle |
| project.lifecycle.transition | product.project.delivery | module.project_lifecycle |
| project.list.open | product.project.delivery | module.project_lifecycle |
| project.risk.list | product.risk.control | module.risk_compliance |
| project.structure.manage | product.execution.collaboration | module.execution_delivery |
| project.task.board | product.execution.collaboration | module.execution_delivery |
| project.task.list | product.execution.collaboration | module.execution_delivery |
| project.weekly_report.open | product.reporting.weekly | module.business_analytics |
| workspace.project.watch | product.workspace.navigation | module.governance_platform |
| workspace.today.focus | product.workspace.navigation | module.governance_platform |

## Unassigned

- none
