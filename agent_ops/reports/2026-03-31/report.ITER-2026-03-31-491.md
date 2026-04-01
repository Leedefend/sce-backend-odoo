# ITER-2026-03-31-491

## Summary
- 开始执行剩余 task-based recommendation 分支的 scratch 验收
- 结论为 `PASS_WITH_RISK`
- 在第一条 `task in progress` 分支上就发现了新的 recommendation correctness 残差，因此本批按规则立即停止，没有继续扩到 `创建任务`

## Scope
- 本批原计划覆盖：
  - `推进任务执行`
  - `创建任务`
- 实际只执行了第一条：
  - 在现有 `in_progress / project.id = 20` 上挂 1 条 scratch `project.task`
  - 正式推进到 `sc_state = in_progress`
  - 检查 overview 与 next-action
  - 同批 cleanup

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-491.yaml` → `PASS`
- runtime scratch audit on `project.id = 20` → `PASS_WITH_RISK`

## Runtime facts
- scratch task：
  - `task_id = 132`
  - `sc_state = in_progress`
  - 通过正式路径完成：
    - `action_prepare_task()`
    - `action_start_task()`
- 但对 `PM / hujun`：
  - `overview.task.count = 13`
  - `overview.task.in_progress = 0`
  - `sc_get_next_actions()` 返回：
    - `actions = []`
- cleanup 后：
  - `task_remaining = false`
  - `overview_task_in_progress_after_cleanup = 0`

## Conclusion
- 新残差已经明确：
  - recommendation 规则 `推进任务执行` 依赖 `task.in_progress > 0`
  - 但 overview 聚合当前没有把 `project.task.sc_state = in_progress` 计入 `task.in_progress`
- 因此这不是样本问题，也不是权限问题，而是 overview/task 统计口径与 recommendation 规则语义不一致
- 按连续迭代 stop 规则，本批不能继续去做 `创建任务` 验收，必须先开一张窄实现批次修 task in-progress count 口径

## Risk
- 结果：`PASS_WITH_RISK`
- 风险点：
  - 只要 `overview.task.in_progress` 继续基于错误口径，`推进任务执行` recommendation 会持续漏判
  - 在修这个口径之前继续验收 `创建任务` 没有意义，因为 task 相关 recommendation 基线已不可信

## Rollback
- 本批 scratch task 已在同批清理，无 runtime 残留需要额外回滚
- 如需撤回治理文件：
  - `git restore agent_ops/tasks/ITER-2026-03-31-491.yaml`
  - `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-491.md`
  - `git restore agent_ops/state/task_results/ITER-2026-03-31-491.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 不能继续自动扩面
- 需要新开一张窄实现批次，只修 overview `task.in_progress` 的统计口径，并回归验证 `推进任务执行` recommendation 恢复
