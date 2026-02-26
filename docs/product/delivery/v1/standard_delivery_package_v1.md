# Standard Delivery Package V1

## Scope
- Delivery phase: A (2-week delivery preparation)
- Module count: 9 (<=10)
- User-facing entry rule: all module entries resolve to scene/menu, no abstract-only module.

## Included Modules

| Module | Target Users | Core Value | Entry (scene/menu) | Key Models |
|---|---|---|---|---|
| 项目立项与台账 | PM, 采购经理 | 完成立项、台账建立、基础资料归档 | `projects.intake`, `projects.list`, `projects.ledger` | `project.project` |
| 项目执行与任务协同 | PM | 跟踪进度、风险、周报，形成执行闭环 | `projects.dashboard`, `projects.dashboard_showcase` | `project.task`, `project.project` |
| 采购与物资协同 | 采购经理, PM | 物资计划与采购执行联动项目侧跟踪 | `cost.project_boq`, `projects.ledger` | `material.plan`, `purchase.order` |
| 付款申请与审批 | 财务, PM | 付款申请发起与审批中心处理 | `finance.payment_requests`, `finance.center` | `payment.request` |
| 资金与结算台账 | 财务 | 支付、资金、结算台账沉淀与对账 | `finance.payment_ledger`, `finance.treasury_ledger`, `finance.settlement_orders` | `account.payment`, `settlement.order` |
| 成本预算与利润分析 | PM, 财务 | 预算、成本、利润、进度联动分析 | `cost.project_budget`, `cost.project_cost_ledger`, `cost.profit_compare` | `project.budget`, `project.cost.ledger` |
| 经营指标与领导看板 | 老板/领导 | 经营指标、项目全局、异常洞察 | `portal.dashboard`, `finance.operating_metrics` | `operating.metrics` |
| 生命周期与治理审计 | 管理员, 老板/领导 | 能力矩阵、场景治理与审计可追溯 | `portal.lifecycle`, `portal.capability_matrix` | `capability.registry`, `scene.registry` |
| 主数据与工作台 | 全角色 | 字典配置与默认工作台入口 | `data.dictionary`, `default` | `ir.model.data`, `res.users` |

## Boundary

### In Scope (V1)
- PM / 财务 / 采购 / 老板四类关键旅程所需入口与对象。
- 与 `system.init` / `ui.contract` / `execute_button` 直接相关的用户路径。

### Out of Scope (V1)
- `scene_smoke_default` 及内部 smoke/debug 入口。
- 新增 capability、重构核心契约、跨行业扩展。

## Notes
- 本文档对应映射产物：`docs/product/delivery/v1/module_scene_capability_map.md`
- 机器可用产物：`artifacts/product/module_scene_capability_map.json`
