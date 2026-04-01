# ITER-2026-04-01-520

## Summary
- 正式分类了 `quota import` 家族
- 结论为 `PASS`
- 当前 `quota import` 可以并入 clean representative config-admin governance family 集合

## Scope
- 本批为 audit-first governance family classification
- 代表入口：
  - [quota_import_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/support/quota_import_views.xml)
    的 `menu_quota_import_wizard / action_quota_import_wizard`
- 角色样本：
  - `PM / hujun`
  - `finance / jiangyijiao`
  - `executive / wutao`
  - `business_admin / admin`

## Repository facts
- [quota_import_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/support/quota_import_views.xml)
  定义 `action_quota_import_wizard -> quota.import.wizard`
- [action_groups_patch.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/security/action_groups_patch.xml)
  将 `action_quota_import_wizard` 显式收敛到 `group_sc_cap_config_admin`
- [quota_import_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/support/quota_import_views.xml)
  的 `menu_quota_import_wizard` 也直接挂在 `group_sc_cap_config_admin`
- [ir.model.access.csv](/mnt/e/sc-backend-odoo/addons/smart_construction_core/security/ir.model.access.csv)
  对 `quota.import.wizard` 只给了 `group_sc_cap_config_admin` 全权限，没有 delivered-role 读面

## Runtime facts
- `PM / hujun` 与 `finance / jiangyijiao`：
  - `menu_quota_import_wizard` 不可见
  - `quota.import.wizard` 的 `read/create/write/unlink` 全部为 `False`
- `executive / wutao` 与 `business_admin / admin`：
  - `menu_quota_import_wizard` 可见
  - `quota.import.wizard` 的 `read/create/write/unlink` 全部为 `True`
- action 本身可被读取，但 delivered-role 用户面没有误暴露菜单入口

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-520.yaml` → `PASS`
- repository audit → `PASS`
- runtime audit on `sc_odoo` → `PASS`

## Conclusion
- `quota import` 当前是 clean representative config-admin governance family
- 当前没有发现菜单、action 与模型 ACL 之间的 runtime residual
- 这条家族的真实语义是纯治理面，不属于 delivered-role secondary family

## Risk
- 结果：`PASS`
- 剩余风险：
  - 本批只覆盖 wizard 入口与 ACL/菜单边界
  - 未展开导入执行后的业务副作用链路；如需验证，应另开更窄 admin 执行批次

## Rollback
- 本批为审计批次，无业务代码需要回滚
- 如需撤回治理文件：
  - `git restore agent_ops/tasks/ITER-2026-04-01-520.yaml`
  - `git restore agent_ops/reports/2026-04-01/report.ITER-2026-04-01-520.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-01-520.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 继续自动推进
- 新开下一张低风险 config-admin 批次，正式分类 `workflow` 家族
