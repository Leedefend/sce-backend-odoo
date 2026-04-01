# ITER-2026-04-01-511

## Summary
- 选定新的候选非首批流程家族为 `dictionary / quota center / 业务字典`
- 结论为 `PASS_WITH_RISK`
- 新的真实 residual 已确认：`action_project_quota_center` 对 delivered roles 菜单可见，但 runtime 执行会撞上 `ir.actions.client` 访问限制

## Scope
- 本批为 audit-first 分类批次
- 代表入口：
  - [dictionary_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/support/dictionary_views.xml)
    的 `action_project_dictionary`
  - [dictionary_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/support/dictionary_views.xml)
    的 `action_project_dictionary_sub_item`
  - [dictionary_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/support/dictionary_views.xml)
    的 `action_project_quota_center`
- 角色样本：
  - `PM / hujun`
  - `finance / jiangyijiao`
  - `executive / wutao`
  - `business_admin / admin`

## Repository facts
- [dictionary_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/support/dictionary_views.xml)
  中：
  - `action_project_dictionary` 和各分类型 `act_window` 入口都挂在 `project.dictionary`
  - `action_project_quota_center` 是 `ir.actions.client`
- [action_groups_patch.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/security/action_groups_patch.xml)
  只对 `act_window` 类字典 action 追加了 `group_sc_cap_data_read`
- [ir.model.access.csv](/mnt/e/sc-backend-odoo/addons/smart_construction_core/security/ir.model.access.csv)
  对 `project.dictionary` 的 ACL 梯度为：
  - `data_read`：只读
  - `config_admin`：可写

## Runtime facts
- `action_project_dictionary` 与 `action_project_dictionary_sub_item`
  在四个样本角色下都可正常读取，`res_model = project.dictionary`
- `project.dictionary` 模型权限在当前 `sc_odoo` runtime 上表现为：
  - `PM / finance`：`read = True`, `create/write/unlink = False`
  - `executive / business_admin`：`read/create/write/unlink = True`
- `menu_sc_data_center`、`menu_sc_dictionary`、`menu_sc_dictionary_root`、
  `menu_project_quota_root` 在四个样本角色下都可见
- 但 `action_project_quota_center` 在 runtime 上出现稳定分裂：
  - `PM / finance / executive`：`AccessError`，原因是无权读取
    `ir.actions.client`
  - `business_admin / admin`：可正常读取 client action，`tag = project_quota_center`

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-511.yaml` → `PASS`
- repository audit → `PASS`
- runtime audit on `sc_odoo` → `PASS_WITH_RISK`

## Conclusion
- `dictionary / quota center / 业务字典` 当前不能判为 clean representative family
- 问题已经收窄为：
  - `project.dictionary` 的 window-action 读面基本可分类
  - 但 `定额中心（左树右明细）` 这条 `ir.actions.client` 入口对 delivered roles
    存在“菜单可见、动作不可执行”的 runtime residual

## Risk
- 结果：`PASS_WITH_RISK`
- 剩余风险：
  - 该 residual 不是样本不足，而是 action 类型与 runtime 权限边界未对齐
  - 在修复 `action_project_quota_center` 之前，不能把 dictionary/quota 家族整体并入 clean family 集合

## Rollback
- 本批为审计批次，无业务代码需要回滚
- 如需撤回治理文件：
  - `git restore agent_ops/tasks/ITER-2026-04-01-511.yaml`
  - `git restore agent_ops/reports/2026-04-01/report.ITER-2026-04-01-511.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-01-511.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 连续迭代必须在这里停住
- 下一步需要新开一张窄实现/治理批次，只处理 `action_project_quota_center` 的 delivered-role 可执行性，优先查清：
  - 是菜单/动作挂组不对齐
  - 还是 client-action 读取路径需要改成更安全的 follow-through 方式
