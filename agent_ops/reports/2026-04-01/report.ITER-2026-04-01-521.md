# ITER-2026-04-01-521

## Summary
- 正式分类了 `workflow` 家族
- 结论为 `PASS`
- 当前 `workflow` 可以并入 clean representative config-admin governance family 集合

## Scope
- 本批为 audit-first governance family classification
- 代表入口：
  - [menu.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/menu.xml)
    的 `menu_sc_workflow_root`
  - [workflow_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/core/workflow_views.xml)
    的 `action_sc_workflow_def / action_sc_workflow_instance`
- 角色样本：
  - `PM / hujun`
  - `finance / jiangyijiao`
  - `executive / wutao`
  - `business_admin / admin`

## Repository facts
- [menu.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/menu.xml)
  提供独立的 `menu_sc_workflow_root`
- [action_groups_patch.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/security/action_groups_patch.xml)
  将 `action_sc_workflow_def / action_sc_workflow_instance` 显式收敛到
  `group_sc_cap_config_admin`
- [ir.model.access.csv](/mnt/e/sc-backend-odoo/addons/smart_construction_core/security/ir.model.access.csv)
  对 `sc.workflow.def / sc.workflow.instance` 仅配置 `group_sc_cap_config_admin` 的全权限
- [workflow_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/core/workflow_views.xml)
  定义两条 canonical action，分别落到 `sc.workflow.def` 与
  `sc.workflow.instance`

## Runtime facts
- `PM / hujun` 与 `finance / jiangyijiao`：
  - `menu_sc_workflow_root` 不可见
  - `sc.workflow.def / sc.workflow.instance` 的 `read/create/write/unlink` 全部为 `False`
- `executive / wutao` 与 `business_admin / admin`：
  - `menu_sc_workflow_root` 可见
  - 两个 workflow 模型的 `read/create/write/unlink` 全部为 `True`
- action 本身可被读取，但 delivered-role 用户面没有暴露 workflow 菜单入口

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-521.yaml` → `PASS`
- repository audit → `PASS`
- runtime audit on `sc_odoo` → `PASS`

## Conclusion
- `workflow` 当前是 clean representative config-admin governance family
- 先前 secondary-family 主线里出现的 direct-action 假阳性，不构成当前治理面目标线的 residual
- 当前没有发现 workflow 菜单、action 与模型权限之间的 delivered-role runtime 错位

## Risk
- 结果：`PASS`
- 剩余风险：
  - 本批未展开 workflow definition/instance 的更深 mutation path
  - 如需验证流程定义编辑、副作用或配置发布链，应另开更窄治理批次

## Rollback
- 本批为审计批次，无业务代码需要回滚
- 如需撤回治理文件：
  - `git restore agent_ops/tasks/ITER-2026-04-01-521.yaml`
  - `git restore agent_ops/reports/2026-04-01/report.ITER-2026-04-01-521.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-01-521.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 继续自动推进
- 新开下一张低风险 config-admin 筛选批次，判断是否还存在自然未覆盖的治理家族
