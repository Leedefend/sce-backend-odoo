# Scene Inventory Draft Diff Report

更新时间：2026-03-14 20:12:33

## Summary

- `current_count`: 14
- `draft_count`: 22
- `added_count`: 8
- `removed_count`: 0
- `changed_count`: 17
- `focus_changed_count`: 14

## Added Scenes

- data.dictionary
- my_work.workspace
- portal.capability_matrix
- portal.dashboard
- portal.lifecycle
- projects.dashboard
- projects.dashboard_showcase
- scene_smoke_default

## Removed Scenes

- 无

## Focus Field Diff

| scene_key | field | current | draft |
| --- | --- | --- | --- |
| contract.center | next_action | 维护合同角色策略与风险动作模板 | 维护角色策略与数据契约稳定性 |
| contracts.workspace | next_action | 维护合同工作台角色动作与风险策略 | 维护角色策略与数据契约稳定性 |
| cost.analysis | next_action | 维护角色化指标策略与模板复用 | 维护角色策略与数据契约稳定性 |
| cost.cost_compare | next_action | 维护成本对比角色动作与异常策略 | 维护角色策略与数据契约稳定性 |
| cost.project_cost_ledger | next_action | 维护台账角色动作与偏差闭环策略 | 维护角色策略与数据契约稳定性 |
| finance.center | next_action | 维护审批角色编排与结算联动策略 | 维护角色策略与数据契约稳定性 |
| finance.payment_requests | next_action | 维护审批角色编排与风险动作模板 | 维护角色策略与数据契约稳定性 |
| finance.settlement_orders | next_action | 维护结算角色动作与风险闭环策略 | 维护角色策略与数据契约稳定性 |
| finance.workspace | next_action | 维护资金角色编排与异常策略 | 维护角色策略与数据契约稳定性 |
| project.management | next_action | 持续优化角色化指标与动作链路 | 维护角色策略与数据契约稳定性 |
| projects.intake | next_action | 维护角色策略与动作模板稳定性 | 维护角色策略与数据契约稳定性 |
| projects.ledger | next_action | 维护台账角色策略与风险联动稳定性 | 维护角色策略与数据契约稳定性 |
| projects.list | next_action | 维护列表角色策略与入口编排稳定性 | 维护角色策略与数据契约稳定性 |
| risk.center | next_action | 进入主线后补齐角色策略与数据契约 | 补齐角色策略与数据契约升级到R3 |

## Full Field Diff

| scene_key | field | current | draft |
| --- | --- | --- | --- |
| contract.center | next_action | 维护合同角色策略与风险动作模板 | 维护角色策略与数据契约稳定性 |
| contracts.workspace | next_action | 维护合同工作台角色动作与风险策略 | 维护角色策略与数据契约稳定性 |
| cost.analysis | next_action | 维护角色化指标策略与模板复用 | 维护角色策略与数据契约稳定性 |
| cost.cost_compare | next_action | 维护成本对比角色动作与异常策略 | 维护角色策略与数据契约稳定性 |
| cost.project_cost_ledger | next_action | 维护台账角色动作与偏差闭环策略 | 维护角色策略与数据契约稳定性 |
| finance.center | next_action | 维护审批角色编排与结算联动策略 | 维护角色策略与数据契约稳定性 |
| finance.payment_requests | name | 付款收款申请 | 付款申请审批 |
| finance.payment_requests | next_action | 维护审批角色编排与风险动作模板 | 维护角色策略与数据契约稳定性 |
| finance.settlement_orders | next_action | 维护结算角色动作与风险闭环策略 | 维护角色策略与数据契约稳定性 |
| finance.workspace | next_action | 维护资金角色编排与异常策略 | 维护角色策略与数据契约稳定性 |
| project.management | route_target | `/pm/dashboard` | `/s/project.management` |
| project.management | next_action | 持续优化角色化指标与动作链路 | 维护角色策略与数据契约稳定性 |
| projects.intake | next_action | 维护角色策略与动作模板稳定性 | 维护角色策略与数据契约稳定性 |
| projects.ledger | name | 项目台账 | 项目台账（试点） |
| projects.ledger | next_action | 维护台账角色策略与风险联动稳定性 | 维护角色策略与数据契约稳定性 |
| projects.list | next_action | 维护列表角色策略与入口编排稳定性 | 维护角色策略与数据契约稳定性 |
| risk.center | next_action | 进入主线后补齐角色策略与数据契约 | 补齐角色策略与数据契约升级到R3 |

