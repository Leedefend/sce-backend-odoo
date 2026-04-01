# ITER-2026-03-31-494

## Summary
- 审计了 fresh project 上 auto-task 的来源
- 结论为 `PASS_WITH_RISK`
- 来源已经明确：不是 `in_progress` 特有行为，而是 `project.project.create()` 后的通用 bootstrap

## Scope
- 本批为 audit-only
- 不改代码、不改 runtime 数据
- 结合：
  - repository tracing
  - bounded runtime observation

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-494.yaml` → `PASS`
- repository + runtime audit → `PASS_WITH_RISK`

## Repository facts
- [project_core.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/core/project_core.py#L1065)
  - `project.project.create()` 在 `super().create()` 后会调用：
    - `ProjectCreationService.post_create_bootstrap(projects)`
- [project_creation_service.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/services/project_creation_service.py#L8)
  - `ProjectInitializationService.bootstrap(project)` 明确执行：
    - 如果项目下没有 task
    - 自动创建 `project.task`
    - 名称为 `项目根任务（Project Root Task）`
- [test_project_plan_bootstrap_backend.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/tests/test_project_plan_bootstrap_backend.py#L46)
  - 测试长期显式调用 `_reset_project_tasks(project)`
  - 这进一步说明 fresh project 带 root task 在当前仓库里是已知常态，不是偶发现象

## Runtime facts
- bounded runtime 直接创建 scratch `project.project`：
  - 创建后项目仍是 `lifecycle_state = draft`
  - 未做任何阶段推进
  - 立刻观察到：
    - `task_count_on_create = 1`
    - `task_names = ["项目根任务（Project Root Task）"]`
    - `task_sc_states = ["draft"]`
- cleanup 后：
  - `project_remaining = false`
  - `task_remaining = false`

## Conclusion
- `493` 遇到的 create-task acceptance 阻塞已经被准确分类：
  - 不是 `in_progress` 状态切换单独产生 task
  - 而是 project creation bootstrap 无条件补根任务
- 所以 `创建任务` recommendation 的当前前提
  - `task.count == 0 and task.in_progress == 0`
  在平台当前 bootstrap 语义下，与 fresh project 事实天然冲突

## Risk
- 结果：`PASS_WITH_RISK`
- 风险点：
  - 这已经不是简单验收缺口，而是 recommendation 规则前提与平台 bootstrap 语义之间的产品/架构冲突
  - 不能在没有新治理决策前继续自动推进，因为后续方向会分叉成：
    - 改 rule 前提
    - 改 bootstrap 任务语义
    - 改 acceptance strategy

## Rollback
- 本批 runtime scratch project/task 已同批清理，无残留需要额外回滚
- 如需撤回治理文件：
  - `git restore agent_ops/tasks/ITER-2026-03-31-494.yaml`
  - `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-494.md`
  - `git restore agent_ops/state/task_results/ITER-2026-03-31-494.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 不能继续自动推进
- 需要新开一张治理批次，在以下三条里做明确选择后才能继续：
  - 保留 root-task bootstrap，改 `创建任务` rule 前提
  - 保留 rule，调整 bootstrap 不再自动建根任务
  - 保留二者不动，把 `创建任务` 从 recommendation acceptance 基线中剔除并改成 product caveat
