# ITER-2026-04-01-505

## Summary
- 选定第三个代表性非首批流程家族为 `project document / 工程资料`
- 结论为 `PASS`
- 当前 `document` 家族的 canonical action 与模型权限边界清晰，没有发现新的 runtime residual

## Scope
- 本批为 audit-first 分类批次
- 代表入口：
  - [document_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/support/document_views.xml#L91)
    的 `action_sc_project_document`
- 角色样本：
  - `PM / hujun`
  - `finance / jiangyijiao`
  - `executive / wutao`
  - `business_admin / admin`

## Repository facts
- [action_groups_patch.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/security/action_groups_patch.xml#L228)
  将 `action_sc_project_document` 收敛到 `group_sc_cap_project_read`
- [ir.model.access.csv](/mnt/e/sc-backend-odoo/addons/smart_construction_core/security/ir.model.access.csv)
  对 `sc.project.document` 的 ACL 是三层结构：
  - `project_read`：`read = 1`, `write/create/unlink = 0`
  - `project_user`：`read/write/create = 1`, `unlink = 0`
  - `project_manager`：`read/write/create/unlink = 1`
- [document_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/support/document_views.xml)
  定义的是标准 tree/form canonical action，没有新的 dispatch/next/fallback 分支

## Runtime facts
- `action_sc_project_document` 在四个样本角色下都可成功读取，`res_model = sc.project.document`
- `sc.project.document` 模型权限在当前 `sc_odoo` runtime 上表现为：
  - `PM / executive / business_admin`：`read/write/create/unlink = True`
  - `finance`：仅 `read = True`，`write/create/unlink = False`
- 这与仓库 groups/ACL 设计保持一致，没有发现 action 可见性与真实模型权限不一致的残差

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-505.yaml` → `PASS`
- repository audit → `PASS`
- runtime audit on `sc_odoo` → `PASS`

## Conclusion
- 第三个代表性非首批流程家族 `project document / 工程资料` 当前可以判定为 `PASS`
- 至此已完成三条 clean representative family classification：
  - `material plan / 待我审批（物资计划）`
  - `BOQ import / task-from-BOQ / execution-structure / progress-entry`
  - `project document / 工程资料`

## Risk
- 结果：`PASS`
- 剩余风险：
  - 本批审计的是 canonical action + 模型权限边界
  - 如后续要扩到 `document` 状态按钮语义，需要另开更细批次；当前未发现必须阻断的 residual

## Rollback
- 本批为审计批次，无业务代码需要回滚
- 如需撤回治理文件：
  - `git restore agent_ops/tasks/ITER-2026-04-01-505.yaml`
  - `git restore agent_ops/reports/2026-04-01/report.ITER-2026-04-01-505.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-01-505.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 继续自动推进
- 选择下一个代表性非首批流程家族继续分类，优先考虑 `tender / 招投标` 或同等级 secondary family
