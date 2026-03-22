# Product v0.1 Demo Flow

## Demo Goal
- 用一条可连续演示的路径说明 v0.1 已经具备可交付能力。

## Demo Preconditions
- 数据库：`sc_demo`
- 用户：`admin`
- 自定义前端：`http://localhost:5174/`
- 项目上下文存在可用 `project_id`

## Flow
1. 打开 `project.initiation.enter`，完成项目立项。
2. 确认成功结果中的 `suggested_action` 指向 `project.dashboard.enter`。
3. 进入 dashboard，查看当前状态与下一步动作。
4. 从 dashboard `next_actions` 进入 `project.plan_bootstrap.enter`。
5. 在 plan 场景查看计划摘要和轻量任务区块。
6. 从 plan `next_actions` 进入 `project.execution.enter`。
7. 在 execution 场景查看执行任务与执行动作。
8. 触发 `project.execution.advance`，观察 `from_state -> to_state` 变化。
9. 确认页面反馈、chatter 记录与 follow-up activity 已生成。

## Expected Demo Signals
- 四个场景均显示“当前状态 + 下一步动作”。
- 区块独立加载；单区块失败不影响整页。
- `execution.advance` 返回结构稳定，页面展示状态迁移反馈。
- 任务列表来自 `project.task`，不是自建任务体系。

## Demo Evidence
- `artifacts/backend/system_init_latency_budget_guard.json`
- `artifacts/backend/portal_preload_runtime_surface_guard.json`
- `artifacts/backend/product_project_dashboard_baseline_*.json`
- `artifacts/backend/product_project_execution_state_smoke*.json`
