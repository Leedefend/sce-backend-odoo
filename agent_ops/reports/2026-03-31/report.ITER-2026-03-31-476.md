# ITER-2026-03-31-476

## Summary
- 修复了项目 overview / form 上 3 个 object-button 的 runtime ACL 残差
- 收口了 `查看阶段要求` 入口：方法不再依赖 wizard 预创建，overview 按钮也不再对交付角色暴露
- 结论为 `PASS`

## Scope
- 实现修复：
  - `action_open_project_budgets`
  - `action_open_project_contracts`
  - `action_view_my_tasks`
  - `action_view_stage_requirements`
- 视图收口：
  - overview 上的 `action_view_stage_requirements`
- 回归覆盖：
  - backend object-button runtime tests
  - overview 按钮可见性测试

## Changed Files
- [project_project_financial.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/core/project_project_financial.py)
- [project_core.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/core/project_core.py)
- [project_stage_requirements.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/support/project_stage_requirements.py)
- [project_overview_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/core/project_overview_views.xml)
- [test_project_object_button_runtime_backend.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/tests/test_project_object_button_runtime_backend.py)
- [__init__.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/tests/__init__.py)

## Implementation Facts
- [project_project_financial.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/core/project_project_financial.py#L8)
  - `action_open_project_budgets/contracts` 改为通过 `env.ref(...).sudo().read()[0]` 读取 action 定义，避免 caller 撞到 `ir.actions.act_window.view` ACL
- [project_core.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/core/project_core.py#L1493)
  - `action_view_my_tasks` 同样改为 `sudo().read()[0]`
- [project_core.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/core/project_core.py#L1955)
  - `action_view_stage_requirements` 不再预创建 wizard，而是返回未落库 modal action，并只注入默认上下文
- [project_stage_requirements.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/support/project_stage_requirements.py#L107)
  - wizard line `action_go` 读取目标 action 时也改为 `sudo().read()[0]`
- [project_overview_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/core/project_overview_views.xml#L45)
  - `action_view_stage_requirements` 按钮收窄到 `group_sc_super_admin`，不再对交付角色暴露
- [test_project_object_button_runtime_backend.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/tests/test_project_object_button_runtime_backend.py#L41)
  - 新增 PM / executive 的 object-button runtime regression
  - 新增 overview 按钮不暴露给交付角色的回归测试

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-476.yaml` → `PASS`
- `make verify.smart_core` → `PASS`
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_odoo` → `PASS`
- `sc_odoo` runtime audit → `PASS`
  - `PM / hujun`
    - `action_open_project_budgets` → `project.budget`
    - `action_open_project_contracts` → `construction.contract`
    - `action_view_my_tasks` → `project.task`
    - overview 中 `action_view_stage_requirements` 不可见
  - `executive / wutao`
    - 上述 3 个 object-button 全部成功返回 action
    - overview 中 `action_view_stage_requirements` 不可见
  - `business_admin / admin`
    - 上述 3 个 object-button 全部成功返回 action
    - overview 中 `action_view_stage_requirements` 不可见

## Conclusion
- `475` 报出的 object-button runtime ACL 残差已经收口
- 当前实现没有新增 ACL，也没有扩大任何 delivered role 的模型权限
- 阶段要求入口按任务合同处理为“后台方法可安全返回未落库 action，但交付 UI 不再暴露”

## Risk
- 结果：`PASS`
- 残余风险：
  - `action_view_stage_requirements` 的完整交付策略仍未定义；当前只是安全降级，不代表后续业务角色已经获得该 wizard 的正式可用性
  - `sudo().read()[0]` 仅用于读取 action 元数据，后续仍需持续审计更深层目标模型自身 ACL 是否与按钮语义一致

## Rollback
- `git restore addons/smart_construction_core/models/core/project_project_financial.py`
- `git restore addons/smart_construction_core/models/core/project_core.py`
- `git restore addons/smart_construction_core/models/support/project_stage_requirements.py`
- `git restore addons/smart_construction_core/views/core/project_overview_views.xml`
- `git restore addons/smart_construction_core/tests/__init__.py`
- `git restore addons/smart_construction_core/tests/test_project_object_button_runtime_backend.py`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-476.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-476.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 继续开低风险审计批次，检查修复后的 overview/object-button 基线之外，是否还存在二跳入口、wizard follow-through 或备用导航残差
