# ITER-2026-03-31-492

## Summary
- 修复了 overview `task.in_progress` 的统计口径
- 结论为 `PASS`
- `推进任务执行` recommendation 已在 runtime 上恢复命中

## Scope
- 本批为窄实现批次
- 仅变更：
  - [project_overview_service.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/services/project_overview_service.py)
  - [test_project_object_button_runtime_backend.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/tests/test_project_object_button_runtime_backend.py)

## Implementation
- 在 [project_overview_service.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/services/project_overview_service.py) 中，把 task in-progress 聚合条件从：
  - `("state", "=", "in_progress")`
  改为：
  - `("sc_state", "=", "in_progress")`
- 在 [test_project_object_button_runtime_backend.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/tests/test_project_object_button_runtime_backend.py) 增加回归：
  - 新建 task
  - `action_prepare_task()`
  - `action_start_task()`
  - 断言 `overview[project_id]['task']['in_progress'] == 1`

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-492.yaml` → `PASS`
- `make verify.smart_core` → `PASS`
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_odoo` → `PASS`
- runtime scratch audit on `project.id = 20` → `PASS`
  - scratch task 通过正式路径进入 `sc_state = in_progress`
  - `overview.task.in_progress = 4`
  - raw next-action payload 命中：
    - `title = 推进任务执行`
    - `action_ref = action_view_my_tasks`
  - cleanup 后：
    - `task_remaining = false`
    - `overview_task_in_progress_after_cleanup = 3`

## Conclusion
- `491` 识别出的 task in-progress recommendation 残差已经关闭
- 根因确实是 overview 统计读取了错误的任务状态字段
- 修复后，runtime task state 与 recommendation 语义重新一致

## Risk
- 结果：`PASS`
- 剩余风险：
  - 当前 recommendation correctness 链路仅剩 `创建任务` 分支尚未单独 runtime 验收

## Rollback
- 如需回滚本批实现：
  - `git restore addons/smart_construction_core/services/project_overview_service.py`
  - `git restore addons/smart_construction_core/tests/test_project_object_button_runtime_backend.py`
- 如需回滚治理文件：
  - `git restore agent_ops/tasks/ITER-2026-03-31-492.yaml`
  - `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-492.md`
  - `git restore agent_ops/state/task_results/ITER-2026-03-31-492.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 继续下一张低风险批次，执行 `创建任务` recommendation 分支的 scratch runtime 验收
