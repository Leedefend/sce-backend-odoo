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
| projects.intake | 项目立项 | project | `/workbench?scene=projects.intake` | project_management | R1 | smart_construction_scene | 补正式 profile（Form template） |
| projects.list | 项目列表 | project | `/workbench?scene=projects.list` | project_management | R1 | smart_construction_scene | 升级为主线列表场景（R2） |
| project.management | 项目驾驶舱 | project | `/pm/dashboard` | project_management | R2 | smart_construction_scene | 补角色差异与动作策略，冲 R3 |
| projects.ledger | 项目台账 | project | `/workbench?scene=projects.ledger` | project_management | R1 | smart_construction_scene | 与项目主线做统一 profile |
| contract.center | 合同中心 | contract | `/workbench?scene=contract.center` | contract_management | R1 | smart_construction_scene | 对齐 Form/List 模板并升级 R2 |
| contracts.workspace | 合同管理工作台 | contract | `/workbench?scene=contracts.workspace` | contract_management | R1 | smart_construction_scene | Workspace 化，补产品动作 |
| cost.cost_compare | 成本中心 | cost | `/workbench?scene=cost.cost_compare` | cost_management | R1 | smart_construction_scene | 对齐 dashboard template |
| cost.project_cost_ledger | 成本台账 | cost | `/workbench?scene=cost.project_cost_ledger` | cost_management | R1 | smart_construction_scene | 升级到 R2，补 block 编排 |
| cost.analysis | 成本控制工作台 | cost | `/workbench?scene=cost.analysis` | cost_management | R1 | smart_construction_scene | 进入 Wave1 产品化 |
| finance.center | 财务中心 | finance | `/workbench?scene=finance.center` | finance_management | R1 | smart_construction_scene | 与审批链路联动升级 |
| finance.workspace | 资金管理工作台 | finance | `/workbench?scene=finance.workspace` | finance_management | R1 | smart_construction_scene | Workspace 模板升级 R2/R3 |
| finance.payment_requests | 付款收款申请 | finance | `/workbench?scene=finance.payment_requests` | finance_management | R1 | smart_construction_scene | 主线优先升级 |
| finance.settlement_orders | 结算单 | finance | `/workbench?scene=finance.settlement_orders` | finance_management | R1 | smart_construction_scene | 主线优先升级 |

## 使用规则（冻结）

- 新增 `scene` 必须先入本表，未登记不得进入产品化开发。
- `maturity_level`、`owner_module`、`next_action` 为空时视为违规。
- 非主线场景默认停留 `R0/R1`，不进入 Wave1 深度产品化。

