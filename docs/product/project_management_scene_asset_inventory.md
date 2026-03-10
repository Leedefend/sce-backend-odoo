# Project Management Scene Asset Inventory (v0.1)

## 1. Scope
- Scene target: `project.management`
- Goal: reuse current `smart_construction_core` assets to build a project-management dashboard scene, not rebuild core ERP models.

## 2. Reusable Models (confirmed)
- `project.project`: project master / owner / manager / stage / code.
- `project.task`: task and progress context (via project/task views and actions).
- `construction.contract`: contract center, income/expense contracts.
- `project.budget`, `project.cost.ledger`, `project.progress.entry`: cost and progress.
- `payment.request`, `payment.ledger`, `sc.treasury.ledger`, `sc.settlement.order`: finance and cashflow.
- `construction.work.breakdown`, `sc.project.structure`: execution structure/WBS.

## 3. Reusable Actions (confirmed)
- Project domain:
  - `smart_construction_core.action_sc_project_kanban_lifecycle`
  - `smart_construction_core.action_sc_project_list`
  - `smart_construction_core.action_project_dashboard`
  - `smart_construction_core.action_project_initiation`
- Contract domain:
  - `smart_construction_core.action_construction_contract_my`
  - `smart_construction_core.action_construction_contract_income`
  - `smart_construction_core.action_construction_contract_expense`
- Cost domain:
  - `smart_construction_core.action_project_budget`
  - `smart_construction_core.action_project_cost_ledger`
  - `smart_construction_core.action_project_progress_entry`
- Finance domain:
  - `smart_construction_core.action_payment_request`
  - `smart_construction_core.action_payment_ledger`
  - `smart_construction_core.action_sc_settlement_order`
  - `smart_construction_core.action_sc_treasury_ledger`

## 4. Reusable Menus (confirmed)
- `smart_construction_core.menu_sc_project_center`
- `smart_construction_core.menu_sc_project_project` (project ledger pilot)
- `smart_construction_core.menu_sc_contract_center`
- `smart_construction_core.menu_sc_cost_center`
- `smart_construction_core.menu_sc_finance_center`
- `smart_construction_core.menu_payment_request`
- `smart_construction_core.menu_sc_settlement_order`
- `smart_construction_core.menu_sc_treasury_ledger`

## 5. Reusable View Assets (confirmed)
- `views/core/project_views.xml`
- `views/core/project_list_views.xml`
- `views/core/project_overview_views.xml`
- `views/projection/project_dashboard_kanban.xml`
- `views/core/contract_views.xml`
- `views/core/project_budget_views.xml`
- `views/core/payment_request_views.xml`
- `views/core/settlement_views.xml`
- `views/core/workflow_views.xml`
- `views/support/work_breakdown_views.xml`

## 6. Capability Assets (confirmed from registry)
- Project: `project.dashboard.open`, `project.list.open`, `project.risk.list`, `project.structure.manage`
- Contract: `contract.center.open`, `contract.income.track`, `contract.expense.track`
- Cost: `cost.ledger.open`, `cost.budget.manage`, `cost.progress.report`
- Finance: `finance.payment_request.list`, `finance.ledger.payment`, `finance.ledger.treasury`, `finance.settlement.order`

## 7. Gaps for this iteration
- Missing dedicated scene key `project.management` in scene data (added in this round).
- Missing explicit page/zone/block orchestration payload for project management scene (added in this round as skeleton).
- Missing explicit capability-to-zone mapping artifact (added in this round).
- No backend aggregate service yet (`ProjectDashboardService`) and no dedicated intent endpoint yet; scheduled for next round.

## 8. Explicit Out-Of-Scope (this round)
- No model redesign.
- No full workflow refactor.
- No full gantt/multi-project executive analytics.
- No large front-end rewrite.

## 9. Conclusion
- Existing assets are enough to launch `project.management` v0.1 as an orchestration-first scene.
- Next round should build contract + aggregate service + intent handler on top of these reused assets.
