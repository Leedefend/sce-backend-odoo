# 原生动态解析层能力专项审计

## 摘要

- 业务模型数：119
- 审计视图数：238
- 解析能力达标视图：238
- 解析能力缺口视图：0
- 解析错误视图：0
- form 主解析通过：119
- form fallback 通过：119
- tree 主解析通过：119
- tree fallback 通过：119

本报告审计后端动态实时页面解析层作为“运行态观察与契约适配器”的能力。它只判断解析层能否完整观察 Odoo 原生运行态，并不把解析结果作为业务事实或展示授权来源。

## 缺口清单



## form 样本

| domain_group | model | view_type | boundary_status | parser_ok | fallback_ok | arch_field_count | parser_field_count | gaps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| contract | construction.contract | form | parser_capability_ok | true | true | 65 | 65 |  |
| contract | construction.contract.expense | form | parser_capability_ok | true | true | 49 | 49 |  |
| contract | construction.contract.income | form | parser_capability_ok | true | true | 58 | 58 |  |
| contract | construction.work.breakdown | form | parser_capability_ok | true | true | 15 | 15 |  |
| equipment | sc.equipment.plan | form | parser_capability_ok | true | true | 16 | 16 |  |
| equipment | sc.equipment.price | form | parser_capability_ok | true | true | 18 | 18 |  |
| equipment | sc.equipment.request | form | parser_capability_ok | true | true | 16 | 16 |  |
| equipment | sc.equipment.settlement | form | parser_capability_ok | true | true | 17 | 17 |  |
| equipment | sc.equipment.usage | form | parser_capability_ok | true | true | 19 | 19 |  |
| finance | payment.ledger | form | parser_capability_ok | true | true | 11 | 11 |  |
| finance | payment.request | form | parser_capability_ok | true | true | 35 | 35 |  |
| finance | payment.request.line | form | parser_capability_ok | true | true | 20 | 20 |  |
| labor | sc.labor.plan | form | parser_capability_ok | true | true | 15 | 15 |  |
| labor | sc.labor.price | form | parser_capability_ok | true | true | 18 | 18 |  |
| labor | sc.labor.request | form | parser_capability_ok | true | true | 14 | 14 |  |
| labor | sc.labor.settlement | form | parser_capability_ok | true | true | 17 | 17 |  |
| labor | sc.labor.usage | form | parser_capability_ok | true | true | 17 | 17 |  |
| material | sc.material.acceptance | form | parser_capability_ok | true | true | 26 | 26 |  |
| material | sc.material.catalog | form | parser_capability_ok | true | true | 20 | 20 |  |
| material | sc.material.inbound | form | parser_capability_ok | true | true | 22 | 22 |  |
| material | sc.material.outbound | form | parser_capability_ok | true | true | 21 | 21 |  |
| material | sc.material.price | form | parser_capability_ok | true | true | 20 | 20 |  |
| material | sc.material.purchase.request | form | parser_capability_ok | true | true | 18 | 18 |  |
| material | sc.material.rental.order | form | parser_capability_ok | true | true | 18 | 18 |  |
| material | sc.material.rental.plan | form | parser_capability_ok | true | true | 19 | 19 |  |
| material | sc.material.rental.settlement | form | parser_capability_ok | true | true | 20 | 20 |  |
| material | sc.material.rfq | form | parser_capability_ok | true | true | 22 | 22 |  |
| material | sc.material.settlement | form | parser_capability_ok | true | true | 21 | 21 |  |
| material | sc.material.stock.summary | form | parser_capability_ok | true | true | 25 | 25 |  |
| project | project.boq.line | form | parser_capability_ok | true | true | 35 | 35 |  |
| project | project.budget | form | parser_capability_ok | true | true | 17 | 17 |  |
| project | project.budget.cost.alloc | form | parser_capability_ok | true | true | 8 | 8 |  |
| project | project.cost.code | form | parser_capability_ok | true | true | 9 | 9 |  |
| project | project.cost.ledger | form | parser_capability_ok | true | true | 12 | 12 |  |
| project | project.dictionary | form | parser_capability_ok | true | true | 15 | 15 |  |
| project | project.funding.baseline | form | parser_capability_ok | true | true | 7 | 7 |  |
| project | project.material.plan | form | parser_capability_ok | true | true | 15 | 15 |  |
| project | project.milestone | form | parser_capability_ok | true | true | 6 | 6 |  |
| project | project.profit.compare | form | parser_capability_ok | true | true | 11 | 11 |  |
| project | project.progress.entry | form | parser_capability_ok | true | true | 11 | 11 |  |

## tree 样本

| domain_group | model | view_type | boundary_status | parser_ok | fallback_ok | arch_field_count | parser_field_count | gaps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| contract | construction.contract | tree | parser_capability_ok | true | true | 43 | 43 |  |
| contract | construction.contract.expense | tree | parser_capability_ok | true | true | 16 | 16 |  |
| contract | construction.contract.income | tree | parser_capability_ok | true | true | 26 | 26 |  |
| contract | construction.work.breakdown | tree | parser_capability_ok | true | true | 12 | 13 |  |
| equipment | sc.equipment.plan | tree | parser_capability_ok | true | true | 14 | 14 |  |
| equipment | sc.equipment.price | tree | parser_capability_ok | true | true | 16 | 16 |  |
| equipment | sc.equipment.request | tree | parser_capability_ok | true | true | 35 | 35 |  |
| equipment | sc.equipment.settlement | tree | parser_capability_ok | true | true | 30 | 31 |  |
| equipment | sc.equipment.usage | tree | parser_capability_ok | true | true | 34 | 34 |  |
| finance | payment.ledger | tree | parser_capability_ok | true | true | 11 | 12 |  |
| finance | payment.request | tree | parser_capability_ok | true | true | 31 | 32 |  |
| finance | payment.request.line | tree | parser_capability_ok | true | true | 18 | 18 |  |
| labor | sc.labor.plan | tree | parser_capability_ok | true | true | 13 | 13 |  |
| labor | sc.labor.price | tree | parser_capability_ok | true | true | 16 | 16 |  |
| labor | sc.labor.request | tree | parser_capability_ok | true | true | 32 | 32 |  |
| labor | sc.labor.settlement | tree | parser_capability_ok | true | true | 30 | 31 |  |
| labor | sc.labor.usage | tree | parser_capability_ok | true | true | 28 | 28 |  |
| material | sc.material.acceptance | tree | parser_capability_ok | true | true | 17 | 17 |  |
| material | sc.material.catalog | tree | parser_capability_ok | true | true | 18 | 18 |  |
| material | sc.material.inbound | tree | parser_capability_ok | true | true | 40 | 40 |  |
| material | sc.material.outbound | tree | parser_capability_ok | true | true | 16 | 16 |  |
| material | sc.material.price | tree | parser_capability_ok | true | true | 17 | 18 |  |
| material | sc.material.purchase.request | tree | parser_capability_ok | true | true | 29 | 29 |  |
| material | sc.material.rental.order | tree | parser_capability_ok | true | true | 43 | 44 |  |
| material | sc.material.rental.plan | tree | parser_capability_ok | true | true | 16 | 17 |  |
| material | sc.material.rental.settlement | tree | parser_capability_ok | true | true | 24 | 25 |  |
| material | sc.material.rfq | tree | parser_capability_ok | true | true | 18 | 18 |  |
| material | sc.material.settlement | tree | parser_capability_ok | true | true | 31 | 32 |  |
| material | sc.material.stock.summary | tree | parser_capability_ok | true | true | 21 | 21 |  |
| project | project.boq.line | tree | parser_capability_ok | true | true | 34 | 36 |  |
| project | project.budget | tree | parser_capability_ok | true | true | 16 | 17 |  |
| project | project.budget.cost.alloc | tree | parser_capability_ok | true | true | 10 | 10 |  |
| project | project.cost.code | tree | parser_capability_ok | true | true | 11 | 11 |  |
| project | project.cost.ledger | tree | parser_capability_ok | true | true | 12 | 12 |  |
| project | project.dictionary | tree | parser_capability_ok | true | true | 14 | 14 |  |
| project | project.funding.baseline | tree | parser_capability_ok | true | true | 7 | 8 |  |
| project | project.material.plan | tree | parser_capability_ok | true | true | 16 | 16 |  |
| project | project.milestone | tree | parser_capability_ok | true | true | 5 | 6 |  |
| project | project.profit.compare | tree | parser_capability_ok | true | true | 9 | 9 |  |
| project | project.progress.entry | tree | parser_capability_ok | true | true | 11 | 11 |  |
