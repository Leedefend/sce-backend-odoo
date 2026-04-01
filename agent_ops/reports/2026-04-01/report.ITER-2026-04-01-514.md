# ITER-2026-04-01-514

## Summary
- 选定新的候选低风险 secondary family 为 `workflow / business evidence`
- 结论为 `PASS_WITH_RISK`
- 新的真实 residual 已确认：`workflow` 家族当前是“入口可见，但目标模型不可读”的 action-to-model 错位

## Scope
- 本批为 audit-first family selection
- 代表入口：
  - [workflow_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/core/workflow_views.xml)
    的 `action_sc_workflow_def`
  - [workflow_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/core/workflow_views.xml)
    的 `action_sc_workflow_instance`
  - [evidence_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/support/evidence_views.xml)
    的 `action_sc_business_evidence`
- 角色样本：
  - `PM / hujun`
  - `finance / jiangyijiao`
  - `executive / wutao`
  - `business_admin / admin`

## Repository facts
- [action_groups_patch.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/security/action_groups_patch.xml)
  将 `action_sc_workflow_def / instance / workitem / log` 全部挂在
  `group_sc_cap_config_admin`
- [ir.model.access.csv](/mnt/e/sc-backend-odoo/addons/smart_construction_core/security/ir.model.access.csv)
  对 `sc.workflow.*` 也只给了 `group_sc_cap_config_admin` 全量权限
- [ir.model.access.csv](/mnt/e/sc-backend-odoo/addons/smart_construction_core/security/ir.model.access.csv)
  对 `sc.business.evidence` 则是清晰的只读梯度：
  - `project_read / cost_read / finance_read`：只读
  - `config_admin`：可写
- [evidence_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/support/evidence_views.xml)
  的 `action_sc_business_evidence` 在仓库里没有额外 groups 字段

## Runtime facts
- 四个样本角色都能成功读取：
  - `action_sc_workflow_def`
  - `action_sc_workflow_instance`
  - `action_sc_business_evidence`
- 但真实模型权限在当前 `sc_odoo` runtime 上表现为：
  - `PM / finance`
    - `sc.workflow.def read = False`
    - `sc.workflow.instance read = False`
    - `sc.business.evidence read = True`
  - `executive / business_admin`
    - `sc.workflow.def / instance` 为全量可写
    - `sc.business.evidence` 为全量可写

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-514.yaml` → `PASS`
- repository audit → `PASS`
- runtime audit on `sc_odoo` → `PASS_WITH_RISK`

## Conclusion
- 当前阻断点已经明确落在 `workflow` 家族，而不是 `business evidence`
- 问题是：
  - `PM / finance` 能看到 workflow 入口
  - 但 runtime 上没有 `sc.workflow.*` 的读取权限
- 所以 `workflow` 家族当前不能判为 clean representative family

## Risk
- 结果：`PASS_WITH_RISK`
- 剩余风险：
  - 这不是样本不足，而是入口 visibility 与模型 ACL 边界未对齐
  - 在收口 workflow action 可见性或模型读权限之前，不能继续把该家族并入 clean family 集合

## Rollback
- 本批为审计批次，无业务代码需要回滚
- 如需撤回治理文件：
  - `git restore agent_ops/tasks/ITER-2026-04-01-514.yaml`
  - `git restore agent_ops/reports/2026-04-01/report.ITER-2026-04-01-514.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-01-514.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 连续迭代必须在这里停住
- 下一步需要新开一张窄治理/实现批次，只收口 `workflow` 家族的 action-to-model 边界，二选一：
  - 收窄 workflow action/menu，不再让非 `config_admin` 角色看到
  - 或给目标角色补受控 workflow 只读语义
