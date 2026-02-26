# PM User Journey V1

## Goal
从立项到执行形成最小闭环，覆盖项目创建、任务推进、周报反馈。

## Journey Steps
| Step | Entry/Menu | scene_key | intent | Action | Expected Result |
|---|---|---|---|---|---|
| 1 | 项目立项 | `projects.intake` | `ui.contract` | 新建项目基础信息 | 项目记录创建成功并可在列表检索 |
| 2 | 项目列表 | `projects.list` | `ui.contract` | 查看项目列表并筛选目标项目 | 进入目标项目详情 |
| 3 | 项目台账 | `projects.ledger` | `ui.contract` | 补充项目文档与结构信息 | 台账信息完整可追溯 |
| 4 | 项目看板 | `projects.dashboard` | `ui.contract` | 查看任务分布与风险提示 | 看板展示正常，无未知入口跳转 |
| 5 | 任务推进 | `projects.dashboard` | `execute_button` | 触发任务推进/状态动作 | 状态推进成功或返回可解释权限结果 |
| 6 | 周报查看 | `projects.dashboard_showcase` | `ui.contract` | 查看周报聚合与里程碑进展 | 周报与项目状态一致 |

## Trace Notes
- 推荐开启 `?hud=1` 记录关键 `trace_id`。
- 若出现 404，必须对应白名单或语义可解释路径。

## Demo Data Anchor
- 推荐样例项目：`DELIVERY-DEMO-PROJECT-001`（对应 `delivery_minimum_seed.project_id`）。
- 推荐样例任务：`TASK-DEMO-001`、`TASK-DEMO-002`（挂载到样例项目）。
- 若无数据，最小创建步骤：
  - 在 `projects.intake` 新建项目并保存。
  - 在项目下创建至少 2 条任务。
  - 在 `projects.ledger` 补充台账文档后再走看板步骤。
