# Scene Inventory Matrix（Latest）

更新时间：2026-03-14  
适用阶段：Wave 1（主线产品化）

## 分级标准

- `R0` = Registry-only（仅注册/可路由）
- `R1` = Policy-backed（已进入导航策略）
- `R2` = Profiled（已有 scene content / zone / block）
- `R3` = Productized（含角色差异、动作编排、数据策略）

## Matrix

| scene_key | name | domain | route_target | nav_group | maturity_level | owner_module | next_action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| projects.intake | 项目立项 | project | `/s/projects.intake` | project_management | R3 | smart_construction_scene | 维护角色策略与动作模板稳定性 |
| projects.list | 项目列表 | project | `/s/projects.list` | project_management | R3 | smart_construction_scene | 维护列表角色策略与入口编排稳定性 |
| project.management | 项目驾驶舱 | project | `/pm/dashboard` | project_management | R3 | smart_construction_scene | 持续优化角色化指标与动作链路 |
| projects.ledger | 项目台账 | project | `/s/projects.ledger` | project_management | R3 | smart_construction_scene | 维护台账角色策略与风险联动稳定性 |
| contract.center | 合同中心 | contract | `/s/contract.center` | contract_management | R3 | smart_construction_scene | 维护合同角色策略与风险动作模板 |
| contracts.workspace | 合同管理工作台 | contract | `/s/contracts.workspace` | contract_management | R3 | smart_construction_scene | 维护合同工作台角色动作与风险策略 |
| cost.cost_compare | 成本中心 | cost | `/s/cost.cost_compare` | cost_management | R3 | smart_construction_scene | 维护成本对比角色动作与异常策略 |
| cost.project_cost_ledger | 成本台账 | cost | `/s/cost.project_cost_ledger` | cost_management | R3 | smart_construction_scene | 维护台账角色动作与偏差闭环策略 |
| cost.analysis | 成本控制工作台 | cost | `/s/cost.analysis` | cost_management | R3 | smart_construction_scene | 维护角色化指标策略与模板复用 |
| finance.center | 财务中心 | finance | `/s/finance.center` | finance_management | R3 | smart_construction_scene | 维护审批角色编排与结算联动策略 |
| finance.workspace | 资金管理工作台 | finance | `/s/finance.workspace` | finance_management | R3 | smart_construction_scene | 维护资金角色编排与异常策略 |
| finance.payment_requests | 付款收款申请 | finance | `/s/finance.payment_requests` | finance_management | R3 | smart_construction_scene | 维护审批角色编排与风险动作模板 |
| finance.settlement_orders | 结算单 | finance | `/s/finance.settlement_orders` | finance_management | R3 | smart_construction_scene | 维护结算角色动作与风险闭环策略 |
| risk.center | 风险提醒工作台 | risk | `/s/risk.center` | risk_management | R2 | smart_construction_scene | 进入主线后补齐角色策略与数据契约 |
| data.dictionary | 业务字典 | data | `/s/data.dictionary` | data_dictionary | R2 | smart_construction_scene | 补齐角色策略与数据契约升级到R3 |
| my_work.workspace | 我的工作 | my_work | `/s/my_work.workspace` | workspace | R2 | smart_construction_scene | 补齐角色策略与数据契约升级到R3 |
| portal.capability_matrix | 能力矩阵 | portal | `/s/project.management` | workspace | R2 | smart_construction_scene | 补齐角色策略与数据契约升级到R3 |
| portal.dashboard | 工作台 | portal | `/` | workspace | R3 | smart_construction_scene | 维护角色策略与动作链路稳定性 |
| portal.lifecycle | 生命周期驾驶舱 | portal | `/s/projects.dashboard` | workspace | R3 | smart_construction_scene | 维护角色策略与动作链路稳定性 |
| projects.dashboard | 项目驾驶舱 | project | `/pm/dashboard` | project_management | R2 | smart_construction_scene | 补齐角色策略与数据契约升级到R3 |
| projects.dashboard_showcase | 项目驾驶舱（演示） | project | `/s/projects.dashboard_showcase` | project_management | R2 | smart_construction_scene | 补齐角色策略与数据契约升级到R3 |
| scene_smoke_default | Scene Smoke Default | scene_smoke_default | `/workbench?scene=scene_smoke_default` | others | R1 | smart_construction_scene | 保持测试场景最小可用并隔离生产入口 |

## 使用规则（冻结）

- 新增 `scene` 必须先入本表，未登记不得进入产品化开发。
- `maturity_level`、`owner_module`、`next_action` 为空时视为违规。
- 非主线场景默认停留 `R0/R1`，不进入 Wave1 深度产品化。
