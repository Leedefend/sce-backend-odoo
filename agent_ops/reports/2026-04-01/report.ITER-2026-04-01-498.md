# ITER-2026-04-01-498

## Summary
- 执行了 `497` 失败后的恢复批次
- 结论为 `PASS`
- `verify.smart_core` 已恢复，`project_next_action_rules.xml` 的 replay 路径可正常升级加载，并且 runtime 上已把 `创建任务` 提升为 bootstrap-only 场景首条 recommendation

## Scope
- 本批为窄恢复批次
- 仅变更：
  - [project_next_action_rules.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/data/project_next_action_rules.xml)
  - [test_project_object_button_runtime_backend.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/tests/test_project_object_button_runtime_backend.py)

## Implementation
- 保留 next-action seed records 在 `noupdate="1"` 数据段
- 新增可重放的 `function/write` 数据段，受控覆写两条既有 rule：
  - `sc_next_action_update_cost`
  - `sc_next_action_create_task`
- 修正 XML `eval` 引号构造，确保 Odoo loader 正常解析
- 收紧回归断言：
  - runtime 读取到的 rule `sequence / condition_expr` 必须已经是新治理基线
  - bootstrap-only 项目首条 recommendation 必须为 `创建任务`

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-498.yaml` → `PASS`
- `make verify.smart_core` → `PASS`
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_odoo` → `PASS`
- runtime scratch audit → `PASS`

## Runtime facts
- 数据库中的既有 rule 行已更新为：
  - `维护成本台账`: `sequence = 30`
  - `创建任务`: `sequence = 20`
  - `创建任务.condition_expr = task.count <= 1 and task.in_progress == 0`
- fresh bootstrap-only `in_progress` scratch project：
  - `overview.task.count = 1`
  - `overview.task.in_progress = 0`
  - raw next-action payload 首条返回：
    - `title = 创建任务`
    - `action_ref = action_view_my_tasks`
  - 次条仍保留：
    - `title = 维护成本台账`
- cleanup 后：
  - `project_remaining = false`
  - `linked_task_remaining = false`

## Conclusion
- `496` 暴露的 runtime/materialization 断层已经闭合
- `497` 期望达到的 runtime rule row 覆写也已经在本批恢复并验证通过
- 当前 recommendation correctness 主链里，`pending payment / 推进任务执行 / 创建任务` 三条先前未完全收口的分支都已经具备 runtime 证据

## Risk
- 结果：`PASS`
- 残余注意项：
  - `project_next_action_rules.xml` 现在显式依赖 `function/write` 作为 canonical replay 路径；后续若继续新增 `noupdate` rule 调整，必须沿用同一 materialization 模式

## Rollback
- 如需回滚本批实现：
  - `git restore addons/smart_construction_core/data/project_next_action_rules.xml`
  - `git restore addons/smart_construction_core/tests/test_project_object_button_runtime_backend.py`
- 如需回滚治理文件：
  - `git restore agent_ops/tasks/ITER-2026-04-01-498.yaml`
  - `git restore agent_ops/reports/2026-04-01/report.ITER-2026-04-01-498.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-01-498.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 当前这条 recommendation correctness 收口链可视为完成
- 若继续推进，应切到新的独立目标，而不是在本链上继续自动扩面
