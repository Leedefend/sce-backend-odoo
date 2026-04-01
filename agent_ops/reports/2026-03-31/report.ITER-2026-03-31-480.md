# ITER-2026-03-31-480

## Summary
- 修复了 `sc_execute_next_action()` 的两条执行分支残差
- `act_window_xmlid` 分支现在安全读取 action 并归一化字符串 context
- `object_method` 分支现在在 recordset 上注入 context 后再执行方法
- 结论为 `PASS`

## Scope
- 实现修复：
  - `sc_execute_next_action()` act-window dispatch
  - `sc_execute_next_action()` object-method dispatch
- 回归覆盖：
  - delivered-role act-window dispatcher success
  - delivered-role object-method dispatcher success

## Changed Files
- [project_core.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/core/project_core.py)
- [test_project_object_button_runtime_backend.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/tests/test_project_object_button_runtime_backend.py)

## Implementation Facts
- [project_core.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/core/project_core.py#L1575)
  - `act_window_xmlid` 分支改用 `ir.actions.act_window._for_xml_id(action_ref)`
  - 对 `action["context"]` 为字符串的情况引入 `safe_eval` 归一化
  - 统一把 merged context 写回 dict
- [project_core.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/core/project_core.py#L1594)
  - `object_method` 分支改为：
    - `record = self.with_context(ctx)`
    - `method = getattr(record, action_ref, None)`
    - `return method()`
- [test_project_object_button_runtime_backend.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/tests/test_project_object_button_runtime_backend.py#L107)
  - 新增 `sc_execute_next_action()` 的 act-window branch 回归测试
- [test_project_object_button_runtime_backend.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/tests/test_project_object_button_runtime_backend.py#L118)
  - 新增 `sc_execute_next_action()` 的 object-method branch 回归测试

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-480.yaml` → `PASS`
- `make verify.smart_core` → `PASS`
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_odoo` → `PASS`
- `sc_odoo` runtime audit → `PASS`
  - `PM / hujun`
    - `act_window_xmlid: action_construction_contract_my` → `construction.contract`
    - `act_window_xmlid: action_sc_project_manage` → `project.project`
    - `act_window_xmlid: action_project_cost_ledger_my` → `project.cost.ledger`
    - `object_method: action_view_my_tasks` → `project.task`
  - `executive / wutao`
    - 上述 4 条 dispatcher 路径全部成功
  - `business_admin / admin`
    - 上述 4 条 dispatcher 路径全部成功
  - 返回 action 的 `context` 已统一为 `dict`

## Conclusion
- `479` 暴露的 dispatcher-level 残差已经收口
- 当前 next-action surface、fallback、dispatcher 三层在已审计路径上已完成第一轮对齐
- 本批没有新增 ACL，也没有扩大 delivered role 权限

## Risk
- 结果：`PASS`
- 残余风险：
  - 当前验证覆盖的是 representative dispatcher 路径，后续仍应继续审计“推荐是否正确”和“目标模型权限是否真实匹配”
  - 其他尚未经过 `sc_execute_next_action()` 的 action-ref 组合仍可能存在更深残差

## Rollback
- `git restore addons/smart_construction_core/models/core/project_core.py`
- `git restore addons/smart_construction_core/tests/test_project_object_button_runtime_backend.py`
- `git restore agent_ops/tasks/ITER-2026-03-31-480.yaml`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-480.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-480.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 继续开低风险审计批次，检查 next-action “推荐结果 + dispatcher 执行 + 目标模型真实可达性” 是否在 representative 场景上整体一致
