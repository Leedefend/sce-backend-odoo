# Native View Ecosystem Sample Registry v1

## Purpose
Defines the 20+ ecosystem sample pool for next-stage contract completion and acceptance.

## Coverage Buckets
- `form`: 8
- `tree`: 5
- `kanban`: 4
- `search`: 5
- total: 22

## Case List
| Case Key | Model | View Type | Domain | Ready |
|---|---|---|---|---|
| project.project_form_complex | project.project | form | project | yes |
| project.project_tree | project.project | tree | project | yes |
| project.project_kanban | project.project | kanban | project | yes |
| project.project_search | project.project | search | project | yes |
| load_view_form_only | universal | form | platform | yes |
| load_view_non_form_gap | universal | tree/kanban/search | platform | yes |
| button_semantics_cross_path | universal | form | platform | yes |
| relation_x2many_contract | project.project | form | project | yes |
| project.task_form | project.task | form | task | yes |
| project.task_tree | project.task | tree | task | yes |
| project.task_kanban | project.task | kanban | task | yes |
| project.task_search | project.task | search | task | yes |
| construction.contract_form | construction.contract | form | contract | yes |
| construction.contract_tree | construction.contract | tree | contract | yes |
| construction.contract_search | construction.contract | search | contract | yes |
| cost.ledger_form | cost.ledger | form | cost | no |
| cost.ledger_tree | cost.ledger | tree | cost | no |
| cost.ledger_search | cost.ledger | search | cost | no |
| finance.payment_form | finance.payment | form | finance | no |
| finance.payment_tree | finance.payment | tree | finance | no |
| finance.payment_search | finance.payment | search | finance | no |
| mail.thread_form_collab | mail.thread | form | collaboration | no |

## Current Stage Summary
- Ready cases: 15/22
- Next target: push ready cases to 19+ in this round.
