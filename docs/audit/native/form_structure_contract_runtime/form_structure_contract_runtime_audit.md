# v2 表单结构运行态契约审计

## 摘要

- 运行态业务表单契约：119
- 已满足 contract 结构标准：119
- 仍需关注：0
- 契约错误：0
- 边界违规：0
- 已启用结构合同且边界通过：119
- 未启用结构合同，保留原生表单：0
- 契约默认页签投影覆盖：0
- 契约分组语义投影覆盖：119
- 附件契约覆盖：119
- 时间线/日志契约覆盖：119

本报告审计前端实际接收的 Unified Page Contract v2。它用于补充原生 XML/运行态 arch 审计，避免把可由契约层投影解决的缺口误判为需要逐个业务视图改 XML。

## 仍需关注



## 边界违规



## 已启用结构合同样本

| domain_group | model | boundary_status | governance_field_count | structure_field_count | layout_field_count | boundary_issues | layout_outside_structure |
| --- | --- | --- | --- | --- | --- | --- | --- |
| contract | construction.contract | boundary_ok | 53 | 53 | 55 |  |  |
| contract | construction.contract.expense | boundary_ok | 41 | 41 | 43 |  |  |
| contract | construction.contract.income | boundary_ok | 41 | 41 | 43 |  |  |
| contract | construction.work.breakdown | boundary_ok | 12 | 12 | 12 |  |  |
| equipment | sc.equipment.plan | boundary_ok | 11 | 11 | 11 |  |  |
| equipment | sc.equipment.price | boundary_ok | 12 | 12 | 12 |  |  |
| equipment | sc.equipment.request | boundary_ok | 32 | 32 | 32 |  |  |
| equipment | sc.equipment.settlement | boundary_ok | 28 | 28 | 28 |  |  |
| equipment | sc.equipment.usage | boundary_ok | 30 | 30 | 30 |  |  |
| finance | payment.ledger | boundary_ok | 9 | 9 | 9 |  |  |
| finance | payment.request | boundary_ok | 48 | 48 | 50 |  |  |
| finance | payment.request.line | boundary_ok | 14 | 14 | 14 |  |  |
| labor | sc.labor.plan | boundary_ok | 10 | 10 | 10 |  |  |
| labor | sc.labor.price | boundary_ok | 12 | 12 | 12 |  |  |
| labor | sc.labor.request | boundary_ok | 29 | 29 | 29 |  |  |
| labor | sc.labor.settlement | boundary_ok | 28 | 28 | 28 |  |  |
| labor | sc.labor.usage | boundary_ok | 24 | 24 | 24 |  |  |
| material | sc.material.acceptance | boundary_ok | 21 | 21 | 21 |  |  |
| material | sc.material.catalog | boundary_ok | 13 | 13 | 13 |  |  |
| material | sc.material.inbound | boundary_ok | 34 | 34 | 34 |  |  |
| material | sc.material.outbound | boundary_ok | 16 | 16 | 16 |  |  |
| material | sc.material.price | boundary_ok | 16 | 16 | 16 |  |  |
| material | sc.material.purchase.request | boundary_ok | 28 | 28 | 28 |  |  |
| material | sc.material.rental.order | boundary_ok | 41 | 41 | 41 |  |  |
| material | sc.material.rental.plan | boundary_ok | 14 | 14 | 14 |  |  |
| material | sc.material.rental.settlement | boundary_ok | 22 | 22 | 22 |  |  |
| material | sc.material.rfq | boundary_ok | 17 | 17 | 17 |  |  |
| material | sc.material.settlement | boundary_ok | 31 | 31 | 31 |  |  |
| material | sc.material.stock.summary | boundary_ok | 23 | 23 | 23 |  |  |
| project | project.boq.line | boundary_ok | 32 | 32 | 32 |  |  |
| project | project.budget | boundary_ok | 14 | 14 | 14 |  |  |
| project | project.budget.cost.alloc | boundary_ok | 6 | 6 | 6 |  |  |
| project | project.cost.code | boundary_ok | 6 | 6 | 6 |  |  |
| project | project.cost.ledger | boundary_ok | 10 | 10 | 10 |  |  |
| project | project.dictionary | boundary_ok | 12 | 12 | 12 |  |  |
| project | project.funding.baseline | boundary_ok | 5 | 5 | 5 |  |  |
| project | project.material.plan | boundary_ok | 10 | 10 | 12 |  |  |
| project | project.milestone | boundary_ok | 4 | 4 | 4 |  |  |
| project | project.profit.compare | boundary_ok | 10 | 10 | 10 |  |  |
| project | project.progress.entry | boundary_ok | 8 | 8 | 8 |  |  |
| project | project.project | boundary_ok | 67 | 67 | 67 |  |  |
| project | project.project.stage | boundary_ok | 5 | 5 | 5 |  |  |
| project | project.tags | boundary_ok | 1 | 1 | 1 |  |  |
| project | project.task | boundary_ok | 8 | 8 | 8 |  |  |
| project | project.task.type | boundary_ok | 6 | 6 | 6 |  |  |
| project | project.update | boundary_ok | 7 | 7 | 7 |  |  |
| quality | sc.quality.issue | boundary_ok | 26 | 26 | 26 |  |  |
| quality | sc.quality.recheck | boundary_ok | 12 | 12 | 12 |  |  |
| quality | sc.quality.rectification | boundary_ok | 12 | 12 | 12 |  |  |
| safety | sc.safety.disclosure | boundary_ok | 11 | 11 | 11 |  |  |
| safety | sc.safety.issue | boundary_ok | 22 | 22 | 22 |  |  |
| safety | sc.safety.patrol.task | boundary_ok | 11 | 11 | 11 |  |  |
| safety | sc.safety.plan | boundary_ok | 10 | 10 | 10 |  |  |
| safety | sc.safety.recheck | boundary_ok | 12 | 12 | 12 |  |  |
| safety | sc.safety.rectification | boundary_ok | 12 | 12 | 12 |  |  |
| sc_other | sc.account.income.expense.summary | boundary_ok | 16 | 16 | 16 |  |  |
| sc_other | sc.approval.policy | boundary_ok | 11 | 11 | 11 |  |  |
| sc_other | sc.approval.scope | boundary_ok | 5 | 5 | 5 |  |  |
| sc_other | sc.ar.ap.company.summary | boundary_ok | 24 | 24 | 24 |  |  |
| sc_other | sc.ar.ap.project.summary | boundary_ok | 25 | 25 | 25 |  |  |
| sc_other | sc.attendance.checkin | boundary_ok | 11 | 11 | 11 |  |  |
| sc_other | sc.business.entity | boundary_ok | 7 | 7 | 7 |  |  |
| sc_other | sc.check.standard | boundary_ok | 13 | 13 | 13 |  |  |
| sc_other | sc.check.standard.item | boundary_ok | 11 | 11 | 11 |  |  |
| sc_other | sc.company.operation.summary | boundary_ok | 27 | 27 | 27 |  |  |
| sc_other | sc.comprehensive.cost.summary | boundary_ok | 21 | 21 | 21 |  |  |
| sc_other | sc.construction.diary | boundary_ok | 43 | 43 | 43 |  |  |
| sc_other | sc.contract.event | boundary_ok | 22 | 22 | 22 |  |  |
| sc_other | sc.dashboard.cockpit.fact | boundary_ok | 19 | 19 | 19 |  |  |
| sc_other | sc.dictionary | boundary_ok | 3 | 3 | 3 |  |  |
| sc_other | sc.document.admin.document | boundary_ok | 24 | 24 | 24 |  |  |
| sc_other | sc.edition.release.snapshot | boundary_ok | 21 | 21 | 21 |  |  |
| sc_other | sc.expense.claim | boundary_ok | 34 | 34 | 36 |  |  |
| sc_other | sc.expense.reimbursement.summary | boundary_ok | 11 | 11 | 11 |  |  |
| sc_other | sc.financing.loan | boundary_ok | 50 | 50 | 52 |  |  |
| sc_other | sc.fund.account | boundary_ok | 29 | 29 | 29 |  |  |
| sc_other | sc.fund.account.operation | boundary_ok | 33 | 33 | 33 |  |  |
| sc_other | sc.fund.daily.summary | boundary_ok | 6 | 6 | 6 |  |  |
| sc_other | sc.general.contract | boundary_ok | 53 | 53 | 55 |  |  |
| sc_other | sc.hazard.source | boundary_ok | 13 | 13 | 13 |  |  |

## 契约投影覆盖样本

| domain_group | model | classification | notebook_count | page_count | semantic_group_count | gaps |
| --- | --- | --- | --- | --- | --- | --- |
| contract | construction.contract | contract_standardized | 1 | 4 | 10 |  |
| contract | construction.contract.expense | contract_standardized | 1 | 4 | 10 |  |
| contract | construction.contract.income | contract_standardized | 1 | 4 | 10 |  |
| contract | construction.work.breakdown | contract_standardized | 1 | 3 | 6 |  |
| equipment | sc.equipment.plan | contract_standardized | 1 | 4 | 7 |  |
| equipment | sc.equipment.price | contract_standardized | 1 | 3 | 7 |  |
| equipment | sc.equipment.request | contract_standardized | 1 | 4 | 8 |  |
| equipment | sc.equipment.settlement | contract_standardized | 1 | 4 | 8 |  |
| equipment | sc.equipment.usage | contract_standardized | 1 | 4 | 8 |  |
| finance | payment.ledger | contract_standardized | 1 | 3 | 6 |  |
| finance | payment.request | contract_standardized | 1 | 4 | 10 |  |
| finance | payment.request.line | contract_standardized | 1 | 3 | 5 |  |
| labor | sc.labor.plan | contract_standardized | 1 | 4 | 6 |  |
| labor | sc.labor.price | contract_standardized | 1 | 3 | 7 |  |
| labor | sc.labor.request | contract_standardized | 1 | 4 | 7 |  |
| labor | sc.labor.settlement | contract_standardized | 1 | 4 | 8 |  |
| labor | sc.labor.usage | contract_standardized | 1 | 4 | 8 |  |
| material | sc.material.acceptance | contract_standardized | 1 | 4 | 7 |  |
| material | sc.material.catalog | contract_standardized | 1 | 3 | 6 |  |
| material | sc.material.inbound | contract_standardized | 1 | 4 | 9 |  |
| material | sc.material.outbound | contract_standardized | 1 | 4 | 7 |  |
| material | sc.material.price | contract_standardized | 1 | 3 | 6 |  |
| material | sc.material.purchase.request | contract_standardized | 1 | 4 | 8 |  |
| material | sc.material.rental.order | contract_standardized | 1 | 4 | 8 |  |
| material | sc.material.rental.plan | contract_standardized | 1 | 4 | 8 |  |
| material | sc.material.rental.settlement | contract_standardized | 1 | 4 | 8 |  |
| material | sc.material.rfq | contract_standardized | 1 | 4 | 7 |  |
| material | sc.material.settlement | contract_standardized | 1 | 4 | 9 |  |
| material | sc.material.stock.summary | contract_standardized | 1 | 2 | 5 |  |
| project | project.boq.line | contract_standardized | 1 | 4 | 7 |  |
| project | project.budget | contract_standardized | 1 | 3 | 7 |  |
| project | project.budget.cost.alloc | contract_standardized | 1 | 3 | 4 |  |
| project | project.cost.code | contract_standardized | 1 | 3 | 6 |  |
| project | project.cost.ledger | contract_standardized | 1 | 3 | 6 |  |
| project | project.dictionary | contract_standardized | 1 | 2 | 5 |  |
| project | project.funding.baseline | contract_standardized | 1 | 3 | 5 |  |
| project | project.material.plan | contract_standardized | 1 | 4 | 6 |  |
| project | project.milestone | contract_standardized | 1 | 2 | 5 |  |
| project | project.profit.compare | contract_standardized | 1 | 2 | 4 |  |
| project | project.progress.entry | contract_standardized | 1 | 3 | 5 |  |
