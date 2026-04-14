# 项目状态消费者审计 v1

状态：Consumers Audit  
批次：ITER-2026-04-13-1833

## 1. 审计范围

本轮使用限定路径扫描 `smart_construction_core` 内项目相关读侧，不做仓库级全扫。

扫描重点：

- `project.project` 相关 service / handler / model / view；
- dashboard / next_actions / context / insight；
- form/list/kanban 视图状态展示；
- `stage_id` / `stage_name` / `current_stage` / `stage_label` / `stage_explain` 消费点。

## 2. 业务误用收口结果

| 消费点 | 原行为 | 处理结果 |
| --- | --- | --- |
| `ProjectStateExplainService.build()` | `stage_label` 读取 `project.stage_id.display_name` | 改为 `lifecycle_state_label(lifecycle_state)` |
| `ProjectDashboardService.project_payload()` | `stage_name` 读取 `project.stage_id` | 改为 `lifecycle_state_label(project)` |
| `ProjectHeaderBuilder.build()` | `stage_name` / `current_stage` 读取 `project.stage_id` | 改为 `lifecycle_state_label(project)` |
| `BaseProjectBlockBuilder._project_context()` | `stage_label` 读取 `project.stage_id` | 改为 `lifecycle_state_label(project)` |
| `build_project_context()` | `stage_label` 读取 `project.stage_id` | 改为 `lifecycle_state_label(stage)` |
| `ProjectExecutionService` / `CostTrackingService` / `ProjectPlanBootstrapService` summary | `stage_name` 读取 `project.stage_id` | 改为 `lifecycle_state_label(project)` |
| `ProjectInsightService._get_stage()` | 优先读取 `project.stage_id` | 改为优先读取 lifecycle 派生标签 |

结论：限定范围内项目业务读侧直接读取 `project.stage_id` 的误用已收口为 0。

## 3. 保留项分类

| 命中 | 分类 | 结论 |
| --- | --- | --- |
| `project_core.py` 中 `stage_id` | lifecycle 投影写入 / advisory 诊断 | 保留 |
| `project_views.xml` header xpath | 原生 `stage_id` 状态栏替换点 | 保留 |
| `legacy_stage_id` / `legacy_stage_name` | 旧系统审计字段 | 保留 |
| `project.task.stage_id` | 任务状态，不是项目状态 | 保留 |
| `flow_map.current_stage` | 驾驶舱流程阶段，基于 lifecycle + 业务事实生成，不读取 project stage | 保留 |

## 4. 待后续关注

后续若进入动作语义统一专项，应继续检查所有 button/server action 是否只写 `lifecycle_state`，不直接写 `stage_id`。

