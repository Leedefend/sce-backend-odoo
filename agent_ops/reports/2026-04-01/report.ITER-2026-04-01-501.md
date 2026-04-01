# ITER-2026-04-01-501

## Summary
- 执行了 `500` 对应的窄实现批次
- 结论为 `PASS_WITH_RISK`
- `project progress entry` 已修通，但 `execution structure entry` 暴露出新的 `context` 归一化残差

## Scope
- 本批仅变更：
  - [project_core.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/core/project_core.py)
  - [execution_structure_actions_base.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/actions/execution_structure_actions_base.xml)
  - [test_project_object_button_runtime_backend.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/tests/test_project_object_button_runtime_backend.py)

## Implementation
- 将 `_action_open_related()` 从 `env.ref(...).read()[0]` 改为 `ir.actions.act_window._for_xml_id(...)`
- 将 `action_open_boq_import()` 改为安全 action dict 路径，并对字符串 `context` 做归一化
- 将 `action_exec_structure_entry` server action 的 direct branch 改为复用 `project.action_open_exec_wbs()`
- 将 `action_exec_structure_entry` 的 fallback branch 改为使用 `ir.actions.act_window._for_xml_id(...)`
- 新增回归，覆盖 execution-side secondary entrypoints 的 runtime 打开路径

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-501.yaml` → `PASS`
- `make verify.smart_core` → `PASS`
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_odoo` → `PASS`
- runtime audit → `PASS_WITH_RISK`

## Runtime facts
- `project.action_open_project_progress_entry()`：
  - `PM / finance / executive` 现在都可成功返回
  - `res_model = project.progress.entry`
  - 不再报 `ir.actions.act_window.view` ACL
- `action_exec_structure_entry.run()`：
  - `PM / finance / executive` 不再报 `ir.actions.act_window.view` ACL
  - 但统一改为报新的 `ValueError`
  - 根因是 server action 里仍对 `direct_action.get('context')` / `next_action.get('context')`
    直接 `dict(...)`，而 `_for_xml_id()` 返回的 `context` 仍可能是字符串

## Conclusion
- 本批已经关闭了 `progress-entry` 这条 execution-side residual
- 但 `execution structure entry` 还未收口：
  - 原来的 action-view ACL 残差被消掉了
  - 新的实际阻塞点是 `context` 字符串到 `dict` 的归一化缺口
- 因此这批不能判 `PASS`

## Risk
- 结果：`PASS_WITH_RISK`
- 风险点：
  - 继续自动推进会变成新的窄修复批次，不再是当前批次的验证闭环
  - 下一步只需要修 `execution_structure_actions_base.xml` 里的 `context` 归一化，不需要再扩展范围

## Rollback
- 如需回滚本批实现：
  - `git restore addons/smart_construction_core/models/core/project_core.py`
  - `git restore addons/smart_construction_core/actions/execution_structure_actions_base.xml`
  - `git restore addons/smart_construction_core/tests/test_project_object_button_runtime_backend.py`
- 如需回滚治理文件：
  - `git restore agent_ops/tasks/ITER-2026-04-01-501.yaml`
  - `git restore agent_ops/reports/2026-04-01/report.ITER-2026-04-01-501.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-01-501.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 不能继续自动扩面
- 需要新开一张更窄的实现批次，只修 `action_exec_structure_entry` 的 `context` 归一化逻辑
