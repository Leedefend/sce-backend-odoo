# ITER-2026-03-31-495

## Summary
- 按治理决定 `1` 执行了 `创建任务` rule 前提对齐
- 结论为 `PASS_WITH_RISK`
- root-task bootstrap 冲突已经被消掉，但 fresh `in_progress` project 仍优先命中 `维护成本台账`，所以 `创建任务` 还是没有真正露出

## Scope
- 本批为窄实现批次
- 仅变更：
  - [project_next_action_rules.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/data/project_next_action_rules.xml)
  - [test_project_object_button_runtime_backend.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/tests/test_project_object_button_runtime_backend.py)

## Implementation
- 将 `创建任务` 规则条件从：
  - `task.count == 0 and task.in_progress == 0`
  调整为：
  - `task.count <= 1 and task.in_progress == 0`
- 新增回归，验证 bootstrap root task 场景不再因 `task.count == 1` 被直接排除

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-495.yaml` → `PASS`
- `make verify.smart_core` → `PASS`
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_odoo` → `PASS`
- runtime scratch audit → `PASS_WITH_RISK`

## Runtime facts
- scratch `in_progress` project：
  - `overview.task.count = 1`
  - `overview.task.in_progress = 0`
- 但 raw payload 返回的是：
  - `title = 维护成本台账`
  - `action_ref = smart_construction_core.action_project_cost_ledger_my`
- 没有返回：
  - `创建任务`
- cleanup 后：
  - `project_remaining = false`
  - `linked_task_remaining = false`

## Conclusion
- 这批修复关闭了“bootstrap root task 让 create-task 前提天然失败”的冲突
- 但新的实际阻塞点已经显现：
  - `维护成本台账` 规则 `sequence = 20`
  - `创建任务` 规则 `sequence = 40`
  - fresh `in_progress` project 同时满足：
    - `cost.count == 0`
    - `task.count <= 1`
    - `task.in_progress == 0`
  - 因为 rule service 按 sequence 取前几条，`创建任务` 被更高优先级的成本规则遮住
- 所以剩余问题已经从 bootstrap semantic conflict 转成了 recommendation priority / mutual-exclusion conflict

## Risk
- 结果：`PASS_WITH_RISK`
- 风险点：
  - 继续自动推进会触发新的产品治理决策，而不是简单实现
  - 现在必须明确：
    - `创建任务` 是否应高于 `维护成本台账`
    - 或者二者是否需要互斥条件

## Rollback
- 如需回滚本批实现：
  - `git restore addons/smart_construction_core/data/project_next_action_rules.xml`
  - `git restore addons/smart_construction_core/tests/test_project_object_button_runtime_backend.py`
- 如需回滚治理文件：
  - `git restore agent_ops/tasks/ITER-2026-03-31-495.yaml`
  - `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-495.md`
  - `git restore agent_ops/state/task_results/ITER-2026-03-31-495.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 不能继续自动推进
- 需要新开一张治理批次，在以下两条里选一条：
  - 提升 `创建任务` 优先级，使其在 bootstrap-only 项目上先于 `维护成本台账`
  - 保持优先级不动，但给 `维护成本台账` 或 `创建任务` 增加互斥前提
