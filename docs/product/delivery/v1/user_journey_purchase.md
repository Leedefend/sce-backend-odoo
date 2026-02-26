# Purchase User Journey V1

## Goal
完成采购最小链路：计划 -> 采购执行 -> 入账联动。

## Journey Steps
| Step | Entry/Menu | scene_key | intent | Action | Expected Result |
|---|---|---|---|---|---|
| 1 | BOQ/物资计划 | `cost.project_boq` | `ui.contract` | 查看项目 BOQ 与物资需求 | 需求项可定位 |
| 2 | 项目台账协同 | `projects.ledger` | `ui.contract` | 查看采购关联资料与进度 | 采购上下文完整 |
| 3 | 采购执行动作 | `cost.project_boq` | `execute_button` | 触发采购相关执行动作 | 返回 2xx 或可解释权限拒绝 |
| 4 | 成本台账核对 | `cost.project_cost_ledger` | `ui.contract` | 校验采购结果在成本侧的体现 | 成本数据可追溯 |

## Object Boundary
- 起点对象：`material.plan` / `project.boq`
- 终点对象：`purchase.order` / `project.cost.ledger`

## Demo Data Anchor
- 推荐样例 BOQ：`BOQ-DEMO-001`（绑定 `DELIVERY-DEMO-PROJECT-001`）。
- 推荐样例采购单：`PO-DEMO-001`（由采购执行动作生成或手工创建）。
- 若无数据，最小创建步骤：
  - 在 `cost.project_boq` 录入 1 条物资需求。
  - 执行一次采购动作（`execute_button`）。
  - 在 `cost.project_cost_ledger` 验证成本记录已生成。
