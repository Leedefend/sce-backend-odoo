# v2 表单结构运行态契约审计

## 摘要

- 运行态业务表单契约：119
- 已满足 contract 结构标准：67
- 仍需关注：52
- 契约错误：0
- 契约默认页签投影覆盖：0
- 契约分组语义投影覆盖：119
- 附件契约覆盖：119
- 时间线/日志契约覆盖：119

本报告审计前端实际接收的 Unified Page Contract v2。它用于补充原生 XML/运行态 arch 审计，避免把可由契约层投影解决的缺口误判为需要逐个业务视图改 XML。

## 仍需关注

| domain_group | model | classification | notebook_count | page_count | semantic_group_count | gaps |
| --- | --- | --- | --- | --- | --- | --- |
| finance | payment.ledger | contract_needs_attention |  |  | 5 | missing_contract_notebook;missing_contract_page |
| finance | payment.request | contract_needs_attention |  |  | 11 | missing_contract_notebook;missing_contract_page |
| finance | payment.request.line | contract_needs_attention |  |  | 6 | missing_contract_notebook;missing_contract_page |
| material | sc.material.catalog | contract_needs_attention |  |  | 9 | missing_contract_notebook;missing_contract_page |
| material | sc.material.price | contract_needs_attention |  |  | 9 | missing_contract_notebook;missing_contract_page |
| material | sc.material.stock.summary | contract_needs_attention |  |  | 9 | missing_contract_notebook;missing_contract_page |
| project | project.budget.cost.alloc | contract_needs_attention |  |  | 2 | missing_contract_notebook;missing_contract_page |
| project | project.cost.code | contract_needs_attention |  |  | 2 | missing_contract_notebook;missing_contract_page |
| project | project.cost.ledger | contract_needs_attention |  |  | 4 | missing_contract_notebook;missing_contract_page |
| project | project.funding.baseline | contract_needs_attention |  |  | 2 | missing_contract_notebook;missing_contract_page |
| project | project.milestone | contract_needs_attention |  |  | 3 | missing_contract_notebook;missing_contract_page |
| project | project.profit.compare | contract_needs_attention |  |  | 6 | missing_contract_notebook;missing_contract_page |
| project | project.progress.entry | contract_needs_attention |  |  | 5 | missing_contract_notebook;missing_contract_page |
| project | project.project.stage | contract_needs_attention |  |  | 4 | missing_contract_notebook;missing_contract_page |
| project | project.tags | contract_needs_attention |  |  | 1 | missing_contract_notebook;missing_contract_page |
| project | project.task | contract_needs_attention |  |  | 2 | missing_contract_notebook;missing_contract_page |
| project | project.task.type | contract_needs_attention |  |  | 3 | missing_contract_notebook;missing_contract_page |
| safety | sc.safety.patrol.task | contract_needs_attention |  |  | 4 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.account.income.expense.summary | contract_needs_attention |  |  | 4 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.approval.scope | contract_needs_attention |  |  | 5 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.check.standard | contract_needs_attention |  |  | 3 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.check.standard.item | contract_needs_attention |  |  | 2 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.company.operation.summary | contract_needs_attention |  |  | 5 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.comprehensive.cost.summary | contract_needs_attention |  |  | 7 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.construction.diary | contract_needs_attention |  |  | 8 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.dashboard.cockpit.fact | contract_needs_attention |  |  | 8 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.dictionary | contract_needs_attention |  |  | 1 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.expense.claim | contract_needs_attention |  |  | 9 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.expense.reimbursement.summary | contract_needs_attention |  |  | 4 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.financing.loan | contract_needs_attention |  |  | 6 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.fund.daily.summary | contract_needs_attention |  |  | 4 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.history.todo | contract_needs_attention |  |  | 8 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.invoice.category.summary | contract_needs_attention |  |  | 7 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.invoice.registration | contract_needs_attention |  |  | 8 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.operating.metrics.project | contract_needs_attention |  |  | 10 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.payment.execution | contract_needs_attention |  |  | 10 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.plan.report | contract_needs_attention |  |  | 7 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.project.stage.requirement.item | contract_needs_attention |  |  | 2 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.project.structure | contract_needs_attention |  |  | 5 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.receipt.income | contract_needs_attention |  |  | 9 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.receipt.invoice.line | contract_needs_attention |  |  | 7 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.risk.item | contract_needs_attention |  |  | 4 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.risk.library | contract_needs_attention |  |  | 2 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.salary.summary | contract_needs_attention |  |  | 4 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.settlement.adjustment | contract_needs_attention |  |  | 8 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.tax.deduction.registration | contract_needs_attention |  |  | 9 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.treasury.ledger | contract_needs_attention |  |  | 8 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.treasury.reconciliation | contract_needs_attention |  |  | 7 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.workflow.node | contract_needs_attention |  |  | 3 | missing_contract_notebook;missing_contract_page |
| tender | tender.doc.purchase | contract_needs_attention |  |  | 10 | missing_contract_notebook;missing_contract_page |
| tender | tender.guarantee | contract_needs_attention |  |  | 6 | missing_contract_notebook;missing_contract_page |
| tender | tender.opening | contract_needs_attention |  |  | 6 | missing_contract_notebook;missing_contract_page |

## 契约投影覆盖样本

| domain_group | model | classification | notebook_count | page_count | semantic_group_count | gaps |
| --- | --- | --- | --- | --- | --- | --- |
| finance | payment.ledger | contract_needs_attention |  |  | 5 | missing_contract_notebook;missing_contract_page |
| finance | payment.request | contract_needs_attention |  |  | 11 | missing_contract_notebook;missing_contract_page |
| finance | payment.request.line | contract_needs_attention |  |  | 6 | missing_contract_notebook;missing_contract_page |
| material | sc.material.catalog | contract_needs_attention |  |  | 9 | missing_contract_notebook;missing_contract_page |
| material | sc.material.price | contract_needs_attention |  |  | 9 | missing_contract_notebook;missing_contract_page |
| material | sc.material.stock.summary | contract_needs_attention |  |  | 9 | missing_contract_notebook;missing_contract_page |
| project | project.budget.cost.alloc | contract_needs_attention |  |  | 2 | missing_contract_notebook;missing_contract_page |
| project | project.cost.code | contract_needs_attention |  |  | 2 | missing_contract_notebook;missing_contract_page |
| project | project.cost.ledger | contract_needs_attention |  |  | 4 | missing_contract_notebook;missing_contract_page |
| project | project.funding.baseline | contract_needs_attention |  |  | 2 | missing_contract_notebook;missing_contract_page |
| project | project.milestone | contract_needs_attention |  |  | 3 | missing_contract_notebook;missing_contract_page |
| project | project.profit.compare | contract_needs_attention |  |  | 6 | missing_contract_notebook;missing_contract_page |
| project | project.progress.entry | contract_needs_attention |  |  | 5 | missing_contract_notebook;missing_contract_page |
| project | project.project.stage | contract_needs_attention |  |  | 4 | missing_contract_notebook;missing_contract_page |
| project | project.tags | contract_needs_attention |  |  | 1 | missing_contract_notebook;missing_contract_page |
| project | project.task | contract_needs_attention |  |  | 2 | missing_contract_notebook;missing_contract_page |
| project | project.task.type | contract_needs_attention |  |  | 3 | missing_contract_notebook;missing_contract_page |
| safety | sc.safety.patrol.task | contract_needs_attention |  |  | 4 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.account.income.expense.summary | contract_needs_attention |  |  | 4 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.approval.scope | contract_needs_attention |  |  | 5 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.check.standard | contract_needs_attention |  |  | 3 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.check.standard.item | contract_needs_attention |  |  | 2 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.company.operation.summary | contract_needs_attention |  |  | 5 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.comprehensive.cost.summary | contract_needs_attention |  |  | 7 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.construction.diary | contract_needs_attention |  |  | 8 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.dashboard.cockpit.fact | contract_needs_attention |  |  | 8 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.dictionary | contract_needs_attention |  |  | 1 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.expense.claim | contract_needs_attention |  |  | 9 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.expense.reimbursement.summary | contract_needs_attention |  |  | 4 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.financing.loan | contract_needs_attention |  |  | 6 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.fund.daily.summary | contract_needs_attention |  |  | 4 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.history.todo | contract_needs_attention |  |  | 8 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.invoice.category.summary | contract_needs_attention |  |  | 7 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.invoice.registration | contract_needs_attention |  |  | 8 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.operating.metrics.project | contract_needs_attention |  |  | 10 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.payment.execution | contract_needs_attention |  |  | 10 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.plan.report | contract_needs_attention |  |  | 7 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.project.stage.requirement.item | contract_needs_attention |  |  | 2 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.project.structure | contract_needs_attention |  |  | 5 | missing_contract_notebook;missing_contract_page |
| sc_other | sc.receipt.income | contract_needs_attention |  |  | 9 | missing_contract_notebook;missing_contract_page |
