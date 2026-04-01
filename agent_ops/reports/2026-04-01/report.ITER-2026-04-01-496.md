# ITER-2026-04-01-496

## Summary
- 按治理决定 `1` 执行了 `创建任务` 优先级提升实现
- 结论为 `PASS_WITH_RISK`
- 仓库规则文件已改，但 runtime 数据没有同步更新；fresh bootstrap-only 项目仍先返回 `维护成本台账`

## Scope
- 本批为窄实现批次
- 仅变更：
  - [project_next_action_rules.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/data/project_next_action_rules.xml)
  - [test_project_object_button_runtime_backend.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/tests/test_project_object_button_runtime_backend.py)

## Implementation
- 将 `维护成本台账` 规则顺序从 `20` 调整为 `30`
- 将 `创建任务` 规则顺序从 `40` 调整为 `20`
- 将回归断言收紧为：
  - bootstrap-only 场景首条 recommendation 必须是 `创建任务`

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-496.yaml` → `PASS`
- `make verify.smart_core` → `PASS`
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_odoo` → `PASS`
- runtime scratch audit → `PASS_WITH_RISK`

## Runtime facts
- fresh bootstrap-only scratch `in_progress` project：
  - `overview.task.count = 1`
  - `overview.task.in_progress = 0`
  - raw next-action payload 仍返回：
    - `title = 维护成本台账`
    - `action_ref = smart_construction_core.action_project_cost_ledger_my`
- 进一步 runtime 诊断确认数据库中的 rule 记录仍是旧值：
  - `维护成本台账` 仍为 `sequence = 20`
  - `创建任务` 仍为 `sequence = 40`
  - `创建任务` 条件仍为旧表达式 `task.count == 0 and task.in_progress == 0`
- cleanup 后：
  - `project_remaining = false`
  - `linked_task_remaining = false`

## Conclusion
- 这批实现本身没有触发新的权限或执行层问题
- 真正的阻塞点是数据 materialization 语义：
  - [project_next_action_rules.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/data/project_next_action_rules.xml) 顶层为 `noupdate="1"`
  - 模块升级没有把修改后的 rule sequence / condition 回灌到既有数据库记录
- 所以当前失败不是“优先级策略错误”，而是“优先级变更未进入 runtime 生效面”

## Risk
- 结果：`PASS_WITH_RISK`
- 风险点：
  - 如果继续自动推进，需要新增一张窄批次处理 next-action rule 的 update semantics
  - 在没有显式处理 `noupdate`/既有数据重写前，仓库代码与 runtime 行为会持续分叉

## Rollback
- 如需回滚本批实现：
  - `git restore addons/smart_construction_core/data/project_next_action_rules.xml`
  - `git restore addons/smart_construction_core/tests/test_project_object_button_runtime_backend.py`
- 如需回滚治理文件：
  - `git restore agent_ops/tasks/ITER-2026-04-01-496.yaml`
  - `git restore agent_ops/reports/2026-04-01/report.ITER-2026-04-01-496.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-01-496.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 不能继续自动推进
- 需要新开一张窄实现批次，只处理既有 `sc.project.next_action.rule` 数据的 update semantics
- 候选方向：
  - 对这两条 rule 做受控 XML/函数式重写，确保升级时覆盖既有 sequence 和 condition
  - 或引入一次性数据修正逻辑，把旧 rule 值迁移到当前治理基线
