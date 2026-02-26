# Capability Asset Map v1

- source: capability_registry + release_capability_report + scene_capability_matrix_report
- capability_count: 42
- active_used_count: 41
- structural_only_count: 0
- isolated_count: 1
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
| analytics.dashboard.executive | projects.dashboard | - | executive | ui.contract | active_used |
| analytics.exception.list | finance.operating_metrics | - | executive | ui.contract | active_used |
| analytics.lifecycle.monitor | portal.lifecycle | - | executive,finance,pm | ui.contract | active_used |
| analytics.project.focus | projects.list | - | executive | ui.contract | active_used |
| contract.center.open | projects.ledger | - | executive | ui.contract | active_used |
| contract.expense.track | projects.ledger | - | executive | ui.contract | active_used |
| contract.income.track | projects.ledger | - | executive | ui.contract | active_used |
| contract.settlement.audit | finance.settlement_orders | - | executive | ui.contract | active_used |
| cost.boq.manage | cost.project_boq | - | executive,finance,pm | ui.contract | active_used |
| cost.budget.manage | cost.project_budget | - | executive,finance,pm | ui.contract | active_used |
| cost.ledger.open | cost.project_cost_ledger | - | - | ui.contract | isolated |
| cost.profit.compare | cost.profit_compare | - | executive,finance | ui.contract | active_used |
| cost.progress.report | cost.project_progress | - | executive,finance,pm | ui.contract | active_used |
| finance.approval.center | finance.center | - | executive,finance | ui.contract | active_used |
| finance.exception.monitor | finance.operating_metrics | - | executive,finance | ui.contract | active_used |
| finance.invoice.list | finance.center | - | executive,finance | ui.contract | active_used |
| finance.ledger.payment | finance.payment_ledger | - | executive,finance | ui.contract | active_used |
| finance.ledger.treasury | finance.treasury_ledger | - | executive,finance | ui.contract | active_used |
| finance.metrics.operating | finance.operating_metrics | - | executive,finance | ui.contract | active_used |
| finance.payment_request.form | finance.payment_requests | - | executive,finance | ui.contract | active_used |
| finance.payment_request.list | finance.payment_requests | - | executive,finance | ui.contract | active_used |
| finance.plan.funding | finance.center | - | executive,finance | ui.contract | active_used |
| finance.settlement.order | finance.settlement_orders | - | executive,finance | ui.contract | active_used |
| governance.capability.matrix | portal.capability_matrix | - | executive,finance,pm | ui.contract | active_used |
| governance.runtime.audit | portal.dashboard | - | executive | ui.contract | active_used |
| governance.scene.openability | portal.capability_matrix | - | executive | ui.contract | active_used |
| material.catalog.open | projects.ledger | - | executive,finance,pm | ui.contract | active_used |
| material.procurement.list | projects.ledger | - | executive,finance,pm | ui.contract | active_used |
| project.board.open | projects.ledger | - | executive,finance,pm | ui.contract | active_used |
| project.dashboard.open | projects.dashboard | - | executive,finance,pm | ui.contract | active_used |
| project.document.open | projects.ledger | - | executive,finance,pm | ui.contract | active_used |
| project.initiation.enter | projects.intake | - | executive,finance,pm | ui.contract | active_used |
| project.lifecycle.open | portal.lifecycle | - | executive,finance,pm | ui.contract | active_used |
| project.lifecycle.transition | portal.lifecycle | - | executive,finance,pm | ui.contract | active_used |
| project.list.open | projects.list | - | executive,finance,pm | ui.contract | active_used |
| project.risk.list | projects.ledger | - | executive,finance,pm | ui.contract | active_used |
| project.structure.manage | cost.project_boq | - | executive,finance,pm | ui.contract | active_used |
| project.task.board | projects.ledger | - | executive,finance,pm | ui.contract | active_used |
| project.task.list | projects.ledger | - | executive,finance,pm | ui.contract | active_used |
| project.weekly_report.open | projects.ledger | - | executive,finance,pm | ui.contract | active_used |
| workspace.project.watch | projects.list | - | executive,finance,pm | ui.contract | active_used |
| workspace.today.focus | portal.dashboard | - | executive,finance,pm | ui.contract | active_used |

## Isolated Capabilities

- cost.ledger.open
