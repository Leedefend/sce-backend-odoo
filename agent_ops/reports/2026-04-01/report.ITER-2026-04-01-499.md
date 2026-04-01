# ITER-2026-04-01-499

## Summary
- 新目标线 `非首批流程` 已启动
- 首轮代表家族选择为 `material plan / 待我审批（物资计划）`
- 结论为 `PASS`

## Scope
- 本批仅做仓库与 runtime 审计
- 角色样本：
  - `PM / hujun`
  - `finance / jiangyijiao`
  - `executive / wutao`
  - `business_admin / admin`
- 家族范围：
  - `action_project_material_plan`
  - `action_project_material_plan_my`
  - `action_sc_tier_review_my_material_plan`
  - `project.material.plan` draft create surface

## Repository facts
- [material_plan_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/core/material_plan_views.xml)
  - `action_submit` 仅开放给 `group_sc_cap_material_user`
  - `action_done` / `action_cancel` 仅开放给 `group_sc_cap_material_manager`
  - `action_project_material_plan_my` 仅开放给 `material_user/material_manager`
- [tier_review_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/support/tier_review_views.xml)
  - `待我审批（物资计划）` 只指向 `tier.review` 中 `project.material.plan` 的等待/待处理实例
- [material_plan.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/core/material_plan.py)
  - `action_submit` 需要 `material_user`
  - `action_approve/action_done/action_cancel` 需要 `material_manager`
- 现有测试基线也一致：
  - [perm_matrix.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/tests/perm_matrix.py)
  - [risk_actions.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/tests/risk_actions.py)
  - [test_smoke_security.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/tests/test_smoke_security.py)

## Runtime facts
- 只读角色/入口摸底：
  - `PM / executive / business_admin` 都带 `material_user + material_manager`
  - `finance` 不带 material write 组，模型仅 `read=true`
  - `finance` 对 `action_project_material_plan` 仅保留 canonical 读面；`my material plan / 待我审批（物资计划）` 均不可见
- 现有库样本：
  - `project.material.plan = 0`
  - `tier.review(model='project.material.plan') = 0`
- 低风险 scratch draft audit：
  - `PM` 可创建 `draft` 物资计划，`line_count = 1`
  - `executive` 可创建 `draft` 物资计划，`line_count = 1`
  - `finance` 创建被 ACL 正常拒绝，报 `AccessError`
  - cleanup 后 `plan_remaining = false` 且 `line_remaining = false`

## Conclusion
- `material plan` 目前表现为边界清晰的 secondary flow，不是新的 authority residual
- 首轮非首批流程审计已成功建立：
  - material-domain write flow 对 `PM / executive / business_admin` 开放
  - `finance` 保持只读或不可见，不会意外拿到该 secondary flow 的 draft create surface

## Risk
- 结果：`PASS`
- 观察项：
  - 现有 runtime 中没有真实 `submit/pending` 物资计划样本，因此本批只覆盖到了 draft create / entry surface
  - 若后续要继续验 `待我审批（物资计划）` 的真实待办链，需要单独开更窄的 approval-sample 批次

## Rollback
- 本批为审计批次，无仓库实现改动需要回滚
- 如需撤回治理文件：
  - `git restore agent_ops/tasks/ITER-2026-04-01-499.yaml`
  - `git restore agent_ops/reports/2026-04-01/report.ITER-2026-04-01-499.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-01-499.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 下一张低风险批次可继续审计第二个代表家族：
  - `BOQ import / task-from-BOQ / execution-structure / progress-entry`
