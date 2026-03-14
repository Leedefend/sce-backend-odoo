# Scene Inventory Matrix（Draft from payload）

更新时间：2026-03-14 20:21:22
来源：自动从 scene payload 解析生成

## Matrix

| scene_key | name | domain | route_target | nav_group | maturity_level | owner_module | next_action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| contract.center | 合同中心 | contract | `/s/contract.center` | contract_management | R3 | smart_construction_scene | 维护角色策略与数据契约稳定性 |
| contracts.workspace | 合同管理工作台 | contract | `/s/contracts.workspace` | contract_management | R3 | smart_construction_scene | 维护角色策略与数据契约稳定性 |
| cost.analysis | 成本控制工作台 | cost | `/s/cost.analysis` | cost_management | R3 | smart_construction_scene | 维护角色策略与数据契约稳定性 |
| cost.cost_compare | 成本中心 | cost | `/s/cost.cost_compare` | cost_management | R3 | smart_construction_scene | 维护角色策略与数据契约稳定性 |
| cost.project_cost_ledger | 成本台账 | cost | `/s/cost.project_cost_ledger` | cost_management | R3 | smart_construction_scene | 维护角色策略与数据契约稳定性 |
| data.dictionary | 业务字典 | data | TARGET_MISSING | data_dictionary | R2 | smart_construction_scene | 补齐角色策略与数据契约升级到R3 |
| finance.center | 财务中心 | finance | `/s/finance.center` | finance_management | R3 | smart_construction_scene | 维护角色策略与数据契约稳定性 |
| finance.payment_requests | 付款申请审批 | finance | `/s/finance.payment_requests` | finance_management | R3 | smart_construction_scene | 维护角色策略与数据契约稳定性 |
| finance.settlement_orders | 结算单 | finance | `/s/finance.settlement_orders` | finance_management | R3 | smart_construction_scene | 维护角色策略与数据契约稳定性 |
| finance.workspace | 资金管理工作台 | finance | `/s/finance.workspace` | finance_management | R3 | smart_construction_scene | 维护角色策略与数据契约稳定性 |
| my_work.workspace | 我的工作 | my_work | `/s/my_work.workspace` | workspace | R2 | smart_construction_scene | 补齐角色策略与数据契约升级到R3 |
| portal.capability_matrix | 能力矩阵 | portal | `/s/project.management` | workspace | R2 | smart_construction_scene | 补齐角色策略与数据契约升级到R3 |
| portal.dashboard | 工作台 | portal | `/` | workspace | R2 | smart_construction_scene | 补齐角色策略与数据契约升级到R3 |
| portal.lifecycle | 生命周期驾驶舱 | portal | `/s/projects.dashboard` | workspace | R2 | smart_construction_scene | 补齐角色策略与数据契约升级到R3 |
| project.management | 项目驾驶舱 | project | `/s/project.management` | project_management | R3 | smart_construction_scene | 维护角色策略与数据契约稳定性 |
| projects.dashboard | 项目驾驶舱 | project | `/pm/dashboard` | project_management | R2 | smart_construction_scene | 补齐角色策略与数据契约升级到R3 |
| projects.dashboard_showcase | 项目驾驶舱（演示） | project | TARGET_MISSING | project_management | R2 | smart_construction_scene | 补齐角色策略与数据契约升级到R3 |
| projects.intake | 项目立项 | project | `/s/projects.intake` | project_management | R3 | smart_construction_scene | 维护角色策略与数据契约稳定性 |
| projects.ledger | 项目台账（试点） | project | `/s/projects.ledger` | project_management | R3 | smart_construction_scene | 维护角色策略与数据契约稳定性 |
| projects.list | 项目列表 | project | `/s/projects.list` | project_management | R3 | smart_construction_scene | 维护角色策略与数据契约稳定性 |
| risk.center | 风险提醒工作台 | risk | `/s/risk.center` | risk_management | R2 | smart_construction_scene | 补齐角色策略与数据契约升级到R3 |
| scene_smoke_default | Scene Smoke Default | scene_smoke_default | `/workbench?scene=scene_smoke_default` | others | R2 | smart_construction_scene | 补齐角色策略与数据契约升级到R3 |

