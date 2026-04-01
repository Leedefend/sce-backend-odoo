# ITER-2026-03-31-479

## Summary
- 审计了 next-action follow-through 执行层 `sc_execute_next_action()`
- 结论为 `PASS_WITH_RISK`
- 发现两类新的执行层残差：
  - `act_window_xmlid` 分支仍会撞 `ir.actions.act_window.view` ACL
  - `object_method` 分支调用方式错误，当前会抛 `AttributeError`

## Scope
- 本批仅做仓库与 runtime 审计
- 关注对象：
  - `project.project.sc_execute_next_action()`
  - secondary action dispatch 的 `act_window_xmlid` / `object_method` 两条执行分支
- 角色样本：
  - `PM / hujun`
  - `executive / wutao`
  - `business_admin / admin`

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-479.yaml` → `PASS`
- repository/runtime audit on `sc_odoo` → `PASS_WITH_RISK`

## Repository facts
- [project_core.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/core/project_core.py#L1575)
  - `act_window_xmlid` 分支当前仍是 `self.env.ref(action_ref).read()[0]`
  - 这与 `475/476` 已修过的 object-button ACL 模式一致，仍可能在 caller 侧撞 `ir.actions.act_window.view` 读取限制
- [project_core.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/core/project_core.py#L1594)
  - `object_method` 分支当前是：
    - `method = getattr(self, action_ref, None)`
    - `return method.with_context(ctx)()`
  - 这里的 `method` 是 Python bound method，不是 recordset；因此 `with_context` 调用位置错误

## Runtime facts
- 样本项目：
  - `project.id = 16`
- 对 `PM / hujun` 和 `executive / wutao`
  - `sc_execute_next_action("act_window_xmlid", "...")` 在以下 action 上都未成功返回 action：
    - `smart_construction_core.action_construction_contract_my`
    - `smart_construction_core.action_sc_project_manage`
    - `smart_construction_core.action_project_cost_ledger_my`
    - `smart_construction_core.action_payment_request_my`
  - runtime 日志明确出现：
    - `Access Denied by ACLs ... model: ir.actions.act_window.view`
- 对 `business_admin / admin`
  - 上述 `act_window_xmlid` 分支未返回 action，且因 action `context` 仍是字符串表达式，当前路径上触发：
    - `ValueError: dictionary update sequence element #0 has length 1; 2 is required`
- 对全部样本角色
  - `sc_execute_next_action("object_method", "action_view_my_tasks", ...)` 都触发：
    - `AttributeError: 'function' object has no attribute 'with_context'`

## Conclusion
- `478` 修正了 next-action fallback 暴露面，但 follow-through 执行层还没对齐
- 当前 `sc_execute_next_action()` 不是“入口隐藏问题”，而是：
  - `act_window_xmlid` 执行分支本身不安全
  - `object_method` 执行分支本身有调用错误
- 因此不能继续向更深业务流验收推进

## Risk
- 结果：`PASS_WITH_RISK`
- 风险点：
  - delivered roles 若通过 next-action 执行 act_window 分支，仍可能在动作元数据读取层被吞掉
  - object-method 分支当前对所有角色都不可用
  - `business_admin` 额外暴露出 action `context` 归一化问题，说明执行层不仅有 ACL 风险，还有 action payload 兼容风险

## Rollback
- 本批为只读审计，无实现代码变更需要回滚
- 如需撤回治理文件：
  - `git restore agent_ops/tasks/ITER-2026-03-31-479.yaml`
  - `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-479.md`
  - `git restore agent_ops/state/task_results/ITER-2026-03-31-479.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 需要新开一张窄实现批次，专门修 `sc_execute_next_action()`：
  - `act_window_xmlid` 分支应安全读取 action 元数据并兼容字符串 context
  - `object_method` 分支应在 recordset 上正确注入 context 后再调用方法
