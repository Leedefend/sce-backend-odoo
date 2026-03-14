# project.management Cockpit Metric Semantics & Data Source Matrix (v1)

## 1. Goal and Scope

- This document freezes business semantics for `project.management.dashboard` aggregate metrics.
- Every metric must be traceable to business objects; no technical-field-only or fabricated aggregation.
- Frontend is presentation-only (label/format), not a business metric recomputation layer.

## 2. Global Principles

- Business-first: aggregate from business master/event data.
- Traceable: each metric has explicit model/field source.
- Degradable: fallback is allowed only when still business-semantic.
- Explainable: empty states must state which business chain is missing.

## 3. Metric Semantics Matrix

| Metric Key | Display Name | Business Semantics | Source Model | Source Fields | Fallback Allowed |
| --- | --- | --- | --- | --- | --- |
| `contract_total` | Income Contract Total | Sum of project contracts where `type=out` | `construction.contract` | `amount_total/amount` | No |
| `subcontract_total` | Expense Contract Total | Sum of project contracts where `type=in` | `construction.contract` | `amount_total/amount` | No |
| `executed_amount` | Executed Amount | Sum of income contracts in execution states | `construction.contract` | `amount_total/amount + state` | No |
| `performance_rate` | Performance Rate | `executed_amount / contract_total` | Derived | aggregate formula | No |
| `output_value` | Output Value | Reported business value first, else `contract_total * progress_rate` | `project.project` + `construction.contract` | `output_value_*` / `contract_total` / `progress_rate` | Yes (progress-based) |
| `budget_target` | Target Cost | Budget target of the project | `project.project` | `budget_total` / `budget_active_cost_target` | No |
| `actual_cost` | Actual Cost | Sum of cost ledger amounts | `project.cost.ledger` | `amount/actual_amount` | No |
| `cost_variance` | Cost Variance | `actual_cost - budget_target` | Derived | aggregate formula | No |
| `cost_completion_rate` | Cost Completion Rate | `actual_cost / budget_target` | Derived | aggregate formula | No |
| `receivable` | Receivable | Sum of income contracts | `construction.contract` | `type=out + amount_total/amount` | No |
| `payable` | Payable | Sum of expense contracts | `construction.contract` | `type=in + amount_total/amount` | No |
| `received` | Received | Approved/done receive requests amount | `payment.request` | `type=receive + state + amount` | No |
| `paid` | Paid | Approved/done pay requests amount | `payment.request` | `type=pay + state + amount` | No |
| `receive_pending` | Receive Pending | Pending receive requests amount | `payment.request` | `type=receive + state + amount` | No |
| `pay_pending` | Pay Pending | Pending pay requests amount | `payment.request` | `type=pay + state + amount` | No |
| `gap` | Cash Gap | `receivable - received` | Derived | aggregate formula | No |
| `net_cash` | Net Cashflow | `received - paid` | Derived | aggregate formula | No |

## 3.1 Progress Semantics Matrix (`project.progress`)

| Metric Key | Display Name | Business Semantics | Source Model | Source Fields | Fallback Allowed |
| --- | --- | --- | --- | --- | --- |
| `task_total` | Total Tasks | Total project tasks | `project.task` | count | No |
| `task_done` | Done Tasks | Tasks with `kanban_state=done` | `project.task` | `kanban_state` | No |
| `task_open` | Open Tasks | `task_total - task_done` | Derived | aggregate formula | No |
| `task_critical` | Critical Tasks | High-priority task count | `project.task` | `priority` | No |
| `task_blocked` | Blocked Tasks | Tasks with `kanban_state=blocked` | `project.task` | `kanban_state` | No |
| `task_overdue` | Overdue Tasks | Tasks whose deadline is before today | `project.task` | `date_deadline` | No |
| `completion_percent` | Completion Rate | `task_done / task_total` | Derived | aggregate formula | No |
| `milestone_total` | Total Milestones | Total project milestones | `project.milestone` | count | No |
| `milestone_done` | Done Milestones | Milestones in done/completed status | `project.milestone` | `status` | No |
| `milestone_delay` | Delayed Milestones | Milestones in delay/overdue/blocked status | `project.milestone` | `status` | No |
| `milestone_progress` | Milestone Progress | `milestone_done / milestone_total` | Derived | aggregate formula | No |
| `milestone_upcoming_days` | Days to Next Milestone | Next unfinished milestone planned date minus today | `project.milestone` | `plan_date` | Yes (returns 0 when absent) |
| `critical_path_health` | Critical Path Health | Rule-based level by blocked/overdue thresholds | Derived | policy calculation | No |

## 3.2 Risk-Progress Linkage Semantics (`project.risk`)

| Metric Key | Display Name | Business Semantics | Source Model | Source Fields | Fallback Allowed |
| --- | --- | --- | --- | --- | --- |
| `progress_task_overdue` | Overdue Task Risk Count | Overdue task count of the project | `project.task` | `date_deadline` | No |
| `progress_task_blocked` | Blocked Task Risk Count | Blocked task count of the project | `project.task` | `kanban_state` | No |
| `progress_milestone_delay` | Delayed Milestone Risk Count | Delayed milestone count of the project | `project.milestone` | `status` | No |
| `risk_score` | Risk Score | Composite score with progress linkage signals | Derived | policy calculation | No |
| `risk_level` | Risk Level | Threshold-based level from score | Derived | policy calculation | No |

## 3.3 Cockpit Action Priority Semantics (`header.quick_actions`)

- Actions must be sorted by `pending_count` first, then business priority.
- Allowed v1 action keys:
  - `open_task_overdue`
  - `open_task_blocked`
  - `open_risk_list`
  - `open_payment_requests`
  - `open_project_form` (navigation fallback)
- Frontend must not reorder action priority against backend ordering.

## 4. Explicit Prohibitions

- Do not use `dashboard_invoice_amount` as contract amount semantics.
- Do not use payment/invoice amount as primary output-value semantics.
- Do not let frontend recompute and override cockpit business metrics.
- Do not inject untraceable constants into cockpit aggregate fields.

## 5. Demo Data Backfill Requirements

- Backfill must be persisted in repeatable demo seeds (XML/seed hook), not ad-hoc shell writes.
- Contract metrics must come from `construction.contract` + `construction.contract.line`.
- Cost metrics must come from `project.cost.ledger`.
- Finance metrics must come from `payment.request` with valid state semantics.

## 6. Verification Requirements

- `make verify.project.dashboard.contract` must pass.
- `make verify.demo.release.seed DB_NAME=sc_demo` must pass.
- Core semantics in this document must be covered by a guard script to prevent regression.
