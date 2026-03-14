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
| projects.list | 项目列表 | project | `/s/projects.list` | project_management | R2 | smart_construction_scene | 与项目主线动作联动，补角色差异（冲 R3） |
| project.management | 项目驾驶舱 | project | `/pm/dashboard` | project_management | R3 | smart_construction_scene | 持续优化角色化指标与动作链路 |
| projects.ledger | 项目台账 | project | `/s/projects.ledger` | project_management | R2 | smart_construction_scene | 联动驾驶舱与风险策略（冲 R3） |
| contract.center | 合同中心 | contract | `/s/contract.center` | contract_management | R2 | smart_construction_scene | 补角色差异入口与审批动作（冲 R3） |
| contracts.workspace | 合同管理工作台 | contract | `/s/contracts.workspace` | contract_management | R2 | smart_construction_scene | 补角色化合同动作与风险联动（冲 R3） |
| cost.cost_compare | 成本中心 | cost | `/s/cost.cost_compare` | cost_management | R2 | smart_construction_scene | 补成本异常处置动作与入口联动 |
| cost.project_cost_ledger | 成本台账 | cost | `/s/cost.project_cost_ledger` | cost_management | R2 | smart_construction_scene | 补台账风险策略与闭环动作 |
| cost.analysis | 成本控制工作台 | cost | `/s/cost.analysis` | cost_management | R3 | smart_construction_scene | 维护角色化指标策略与模板复用 |
| finance.center | 财务中心 | finance | `/s/finance.center` | finance_management | R2 | smart_construction_scene | 强化审批链路角色差异动作 |
| finance.workspace | 资金管理工作台 | finance | `/s/finance.workspace` | finance_management | R3 | smart_construction_scene | 维护资金角色编排与异常策略 |
| finance.payment_requests | 付款收款申请 | finance | `/workbench?scene=finance.payment_requests` | finance_management | R2 | smart_construction_scene | 补审批角色差异与动作编排（冲 R3） |
| finance.settlement_orders | 结算单 | finance | `/s/finance.settlement_orders` | finance_management | R2 | smart_construction_scene | 补结算风险闭环动作与联动入口 |

## 使用规则（冻结）

- 新增 `scene` 必须先入本表，未登记不得进入产品化开发。
- `maturity_level`、`owner_module`、`next_action` 为空时视为违规。
- 非主线场景默认停留 `R0/R1`，不进入 Wave1 深度产品化。
