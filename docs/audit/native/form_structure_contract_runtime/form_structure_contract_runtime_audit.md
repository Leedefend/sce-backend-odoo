# v2 表单结构运行态契约审计

## 摘要

- 运行态业务表单契约：115
- 已满足 contract 结构标准：115
- 仍需关注：0
- 契约错误：0
- 契约默认页签投影覆盖：52
- 契约分组语义投影覆盖：115
- 附件契约覆盖：115
- 时间线/日志契约覆盖：115

本报告审计前端实际接收的 Unified Page Contract v2。它用于补充原生 XML/运行态 arch 审计，避免把可由契约层投影解决的缺口误判为需要逐个业务视图改 XML。

## 仍需关注



## 契约投影覆盖样本

| domain_group | model | classification | notebook_count | page_count | semantic_group_count | gaps |
| --- | --- | --- | --- | --- | --- | --- |
| contract | construction.contract | contract_standardized | 1 | 2 | 5 |  |
| contract | construction.contract.expense | contract_standardized | 1 | 3 | 4 |  |
| contract | construction.contract.income | contract_standardized | 1 | 3 | 4 |  |
| contract | construction.work.breakdown | contract_standardized | 1 | 3 | 3 |  |
| equipment | sc.equipment.plan | contract_standardized | 1 | 3 | 4 |  |
| equipment | sc.equipment.price | contract_standardized | 1 | 2 | 4 |  |
| equipment | sc.equipment.request | contract_standardized | 1 | 3 | 4 |  |
| equipment | sc.equipment.settlement | contract_standardized | 1 | 3 | 4 |  |
| equipment | sc.equipment.usage | contract_standardized | 1 | 2 | 4 |  |
| finance | payment.ledger | contract_standardized | 1 | 2 | 4 |  |
| finance | payment.request | contract_standardized | 1 | 4 | 10 |  |
| finance | payment.request.line | contract_standardized | 1 | 3 | 5 |  |
| labor | sc.labor.plan | contract_standardized | 1 | 3 | 4 |  |
| labor | sc.labor.price | contract_standardized | 1 | 2 | 4 |  |
| labor | sc.labor.request | contract_standardized | 1 | 3 | 4 |  |
| labor | sc.labor.settlement | contract_standardized | 1 | 3 | 4 |  |
| labor | sc.labor.usage | contract_standardized | 1 | 3 | 4 |  |
| material | sc.material.acceptance | contract_standardized | 1 | 4 | 6 |  |
| material | sc.material.catalog | contract_standardized | 1 | 3 | 8 |  |
| material | sc.material.inbound | contract_standardized | 1 | 3 | 5 |  |
| material | sc.material.outbound | contract_standardized | 1 | 3 | 5 |  |
| material | sc.material.price | contract_standardized | 1 | 3 | 8 |  |
| material | sc.material.purchase.request | contract_standardized | 1 | 3 | 5 |  |
| material | sc.material.rental.order | contract_standardized | 1 | 3 | 4 |  |
| material | sc.material.rental.plan | contract_standardized | 1 | 3 | 4 |  |
| material | sc.material.rental.settlement | contract_standardized | 1 | 3 | 4 |  |
| material | sc.material.rfq | contract_standardized | 1 | 3 | 5 |  |
| material | sc.material.settlement | contract_standardized | 1 | 3 | 6 |  |
| material | sc.material.stock.summary | contract_standardized | 1 | 2 | 9 |  |
| project | project.boq.line | contract_standardized | 1 | 2 | 13 |  |
| project | project.budget | contract_standardized | 1 | 1 | 3 |  |
| project | project.budget.cost.alloc | contract_standardized | 1 | 1 | 1 |  |
| project | project.cost.code | contract_standardized | 1 | 1 | 1 |  |
| project | project.cost.ledger | contract_standardized | 1 | 2 | 3 |  |
| project | project.dictionary | contract_standardized | 1 | 1 | 2 |  |
| project | project.funding.baseline | contract_standardized | 1 | 1 | 1 |  |
| project | project.material.plan | contract_standardized | 1 | 3 | 2 |  |
| project | project.milestone | contract_standardized | 1 | 1 | 2 |  |
| project | project.profit.compare | contract_standardized | 1 | 1 | 6 |  |
| project | project.progress.entry | contract_standardized | 1 | 2 | 4 |  |
