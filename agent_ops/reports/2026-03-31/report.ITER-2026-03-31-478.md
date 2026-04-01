# ITER-2026-03-31-478

## Summary
- 收口了 `477` 发现的 next-action 二跳残差
- `sc_get_next_actions()` 现在只对 `group_sc_super_admin` 下发 `action_view_stage_requirements` fallback
- 结论为 `PASS`

## Scope
- 实现修复：
  - `sc_get_next_actions()` fallback 对齐
- 回归覆盖：
  - delivered-role fallback suppression
  - super-admin fallback retention

## Changed Files
- [project_core.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/core/project_core.py)
- [test_project_object_button_runtime_backend.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/tests/test_project_object_button_runtime_backend.py)

## Implementation Facts
- [project_core.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/core/project_core.py#L1510)
  - `fallback` 默认改为 `None`
  - 只有 `self.env.user.has_group("smart_construction_core.group_sc_super_admin")` 时，才下发
    `action_view_stage_requirements`
- [test_project_object_button_runtime_backend.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/tests/test_project_object_button_runtime_backend.py#L95)
  - 新增 delivered roles 不再收到 stage-requirements fallback 的回归测试
- [test_project_object_button_runtime_backend.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/tests/test_project_object_button_runtime_backend.py#L100)
  - 新增 super admin 仍保留该 fallback 的回归测试

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-478.yaml` → `PASS`
- `make verify.smart_core` → `PASS`
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_odoo` → `PASS`
- `sc_odoo` runtime audit → `PASS`
  - `PM / hujun` → `fallback = null`
  - `executive / wutao` → `fallback = null`
  - `business_admin / admin` → `fallback = null`
  - `sc_odoo` 中未找到现成 `group_sc_super_admin` 样本用户；该分支由 backend regression test 覆盖

## Conclusion
- `476` 与 `478` 组合后，`action_view_stage_requirements` 已从：
  - overview 静态按钮层
  - next-action fallback 层
  同步对齐到同一可见性策略
- 当前没有新增 ACL，也没有扩大 delivered role 的权限面

## Risk
- 结果：`PASS`
- 残余风险：
  - 运行库缺少现成 super-admin 样本用户，所以 super-admin 分支依赖自动化测试而非 runtime 样本复核
  - 下一步仍应审计 `sc_execute_next_action()` 和其他 follow-through 执行路径，确认二跳执行层没有类似残差

## Rollback
- `git restore addons/smart_construction_core/models/core/project_core.py`
- `git restore addons/smart_construction_core/tests/test_project_object_button_runtime_backend.py`
- `git restore agent_ops/tasks/ITER-2026-03-31-478.yaml`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-478.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-478.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 继续开低风险审计批次，检查 `sc_execute_next_action()` 与其他 follow-through 执行链是否仍有 action metadata / ACL 二跳残差
