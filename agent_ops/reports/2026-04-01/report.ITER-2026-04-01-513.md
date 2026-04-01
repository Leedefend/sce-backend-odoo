# ITER-2026-04-01-513

## Summary
- 复判了 `dictionary / quota center / 业务字典` 家族
- 结论为 `PASS`
- 在 `512` 修正入口路径后，该家族当前可以并入 clean representative non-first-batch family 集合

## Scope
- 本批为 audit-first reclassification
- 代表入口：
  - [dictionary_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/support/dictionary_views.xml)
    的 `action_project_dictionary`
  - [dictionary_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/support/dictionary_views.xml)
    的 `action_project_quota_center_entry`
- 角色样本：
  - `PM / hujun`
  - `finance / jiangyijiao`
  - `executive / wutao`
  - `business_admin / admin`

## Repository facts
- 字典主入口仍是 `project.dictionary` 的 standard window action
- `quota center` 当前通过 `action_project_quota_center_entry` 进入，并复用
  `project.dictionary.action_open_quota_center()` 返回现有 client-action dict
- 本批没有新增 ACL 或 manifest 变化

## Runtime facts
- `action_project_dictionary` 在四个样本角色下都可正常读取，`res_model = project.dictionary`
- `action_project_quota_center_entry.run()` 在四个样本角色下都稳定返回：
  - `type = ir.actions.client`
  - `tag = project_quota_center`
- `project.dictionary` 模型权限在当前 `sc_odoo` runtime 上表现为：
  - `PM / finance`：只读
  - `executive / business_admin`：可写
- 修复后的 quota-center 入口与模型权限边界不再冲突，没有发现新的 runtime residual

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-513.yaml` → `PASS`
- repository/runtime re-audit on `sc_odoo` → `PASS`

## Conclusion
- `dictionary / quota center / 业务字典` 当前可以作为新的 clean representative non-first-batch family
- 已闭环的代表家族继续扩展为：
  - `material plan / 待我审批（物资计划）`
  - `BOQ import / task-from-BOQ / execution-structure / progress-entry`
  - `project document / 工程资料`
  - `tender / 招投标`
  - `contract / 收入合同 / 支出合同`
  - `dictionary / quota center / 业务字典`

## Risk
- 结果：`PASS`
- 剩余风险：
  - 本批复判的是 canonical dictionary/quota entry surface
  - 如后续扩展到 quota import、dictionary admin 维护面，需要另开更细批次；当前没有新的阻断 residual

## Rollback
- 本批为审计批次，无业务代码需要回滚
- 如需撤回治理文件：
  - `git restore agent_ops/tasks/ITER-2026-04-01-513.yaml`
  - `git restore agent_ops/reports/2026-04-01/report.ITER-2026-04-01-513.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-01-513.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 继续自动推进
- 新开下一张低风险筛选批次，选择另一个尚未覆盖且不直接落入 financial 高风险面的 secondary family
