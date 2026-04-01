# ITER-2026-04-01-503

## Summary
- 执行了 `502` 对应的超窄实现批次
- 结论为 `PASS`
- `action_exec_structure_entry` 已不再依赖 server action eval context 里的 `safe_eval`

## Scope
- 本批仅变更：
  - [project_core.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/core/project_core.py)
  - [execution_structure_actions_base.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/actions/execution_structure_actions_base.xml)

## Implementation
- 在 [project_core.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/core/project_core.py#L925)
  新增 `_normalize_action_context()`，把 action `context` 的归一化统一收敛到 Python helper
- 在 [project_core.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/core/project_core.py#L1600)
  复用该 helper 处理 `sc_execute_next_action()` 的 `act_window_xmlid` 分支
- 在 [project_core.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/core/project_core.py#L1637)
  复用该 helper 处理 `action_open_boq_import()` 的字符串 `context`
- 在 [execution_structure_actions_base.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/actions/execution_structure_actions_base.xml#L8)
  删除 server action 内部对 `safe_eval` eval-context 的依赖，改为调用
  `Project._normalize_action_context(...)`

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-503.yaml` → `PASS`
- `make verify.smart_core` → `PASS`
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_odoo` → `PASS`
- runtime audit on `sc_odoo` → `PASS`

## Runtime facts
- `action_exec_structure_entry.run()` 对代表性 delivered roles 现已稳定成功：
  - `PM / hujun`
  - `finance / jiangyijiao`
  - `executive / wutao`
- 三个样本统一返回：
  - `type = ir.actions.client`
  - `tag = display_notification`
  - `params.next.res_model = project.project`
  - `params.next.context` 为 `dict`
- 未再出现：
  - `AccessError: ir.actions.act_window.view`
  - `ValueError`
  - `KeyError: "safe_eval"`

## Conclusion
- `502` 暴露的 execution-structure server-action residual 已收口
- 当前 execution-side secondary entry dispatch 修复链可以判定为 `PASS`

## Risk
- 结果：`PASS`
- 剩余风险：
  - 本批只关闭了 execution-structure entry 的 follow-through residual
  - 下一步应回到上层 secondary-flow 家族复审，确认 `500` 这条家族现在可整体重分类

## Rollback
- `git restore addons/smart_construction_core/models/core/project_core.py`
- `git restore addons/smart_construction_core/actions/execution_structure_actions_base.xml`
- `git restore agent_ops/tasks/ITER-2026-04-01-503.yaml`
- `git restore agent_ops/reports/2026-04-01/report.ITER-2026-04-01-503.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-01-503.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 继续自动推进
- 新开一张低风险复审批次，回到 `500` 的 `BOQ / execution-side` 家族做收口分类
