# Executive User Journey V1

## Goal
老板/领导仅通过只读看板掌握经营与项目风险。

## Journey Steps
| Step | Entry/Menu | scene_key | intent | Action | Expected Result |
|---|---|---|---|---|---|
| 1 | 领导看板 | `portal.dashboard` | `ui.contract` | 打开经营总览看板 | 指标正常渲染 |
| 2 | 经营指标 | `finance.operating_metrics` | `ui.contract` | 查看指标明细与趋势 | 指标可读且不暴露执行入口 |
| 3 | 项目聚焦 | `projects.dashboard_showcase` | `ui.contract` | 查看关键项目状态 | 可见关键状态，不含可执行按钮 |
| 4 | 治理矩阵 | `portal.capability_matrix` | `ui.contract` | 查看能力与入口映射 | 仅可读展示 |

## Permission Notes
- 领导角色默认只读。
- 若触发 `PERMISSION_DENIED`，应为预期保护而非错误。

## Demo Data Anchor
- 推荐指标快照：`OPS-METRIC-DEMO-TODAY`（在 `finance.operating_metrics` 可见）。
- 推荐项目聚焦样例：`DELIVERY-DEMO-PROJECT-001`（在 `projects.dashboard_showcase` 可见）。
- 若无数据，最小创建步骤：
  - 先完成 PM 与财务旅程各 1 次，产生项目与财务数据。
  - 刷新 `portal.dashboard` 与 `finance.operating_metrics` 校验指标加载。
