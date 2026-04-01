# ITER-2026-03-31-493

## Summary
- 对最后一条 `创建任务` recommendation 分支做了 runtime 验收尝试
- 结论为 `PASS_WITH_RISK`
- 当前阻塞点不是权限或 recommendation 逻辑，而是 `in_progress` scratch project 在 runtime 上会自动带出 task，导致 `task.count == 0` 前提无法成立

## Scope
- 本批优先做现有样本发现，再做 bounded scratch project 验收
- 不改代码、不改 ACL、不改 seed

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-493.yaml` → `PASS`
- runtime sample discovery / scratch audit → `PASS_WITH_RISK`

## Runtime facts
- 现有样本发现：
  - 对 `hujun / wutao / admin`
  - 当前 `sc_odoo` 不存在任何 `in_progress` 且 `task.count == 0` 的项目
- scratch project 路径：
  - 通过 `create({lifecycle_state='in_progress', owner_id, manager_id, user_id, location})`
    成功创建 scratch project
  - 但该项目一进入 runtime 就表现为：
    - `overview.task.count = 1`
    - `overview.task.in_progress = 0`
    - next-action 返回的是：
      - `维护成本台账`
    - 不是 `创建任务`
- cleanup 已完成：
  - `project_remaining = false`
  - `linked_task_remaining = false`

## Conclusion
- 当前 `创建任务` recommendation 分支无法被直接验收，不是因为规则本身失效，而是因为 runtime 事实层出现了新的样本语义问题：
  - scratch `in_progress` project 会自动携带 task
  - 因此 `task.count == 0` 条件在当前 runtime 上很难成立
- 这意味着要继续 closing 这条分支，必须先查清：
  - 这个 task 是谁在创建
  - 它是否是平台预期 bootstrap 语义
  - `创建任务` 规则是否本来就不该依赖 “absolute zero tasks”

## Risk
- 结果：`PASS_WITH_RISK`
- 风险点：
  - 在没搞清 auto-task 来源之前，继续硬造 zero-task `in_progress` 项目容易把验收问题升级成 platform bootstrap 语义问题
  - 当前 recommendation correctness 链路只剩这一条未闭合，但它已经不再是简单验收问题

## Rollback
- 本批 scratch project 与 linked task 已同批清理，无 runtime 残留需要额外回滚
- 如需撤回治理文件：
  - `git restore agent_ops/tasks/ITER-2026-03-31-493.yaml`
  - `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-493.md`
  - `git restore agent_ops/state/task_results/ITER-2026-03-31-493.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 不能继续自动推进
- 需要新开一张窄审计/实现批次，先查 `in_progress` scratch project 的 auto-task 来源，再决定是修规则前提、修 bootstrap 语义，还是改 acceptance strategy
