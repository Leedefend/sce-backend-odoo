# ITER-2026-03-31-472

## Summary
- 审计了四川保盛首批交付角色的代表性写路径与审批路径归属
- 结论为 `PASS_WITH_RISK`
- 角色边界总体可分类，但仍有两个“入口可见 vs 写权未落地”的残差需要单开窄批次收口

## Scope
- 本批仅做仓库与 runtime 只读审计
- 角色样本：
  - `PM / hujun`
  - `finance / jiangyijiao`
  - `executive / wutao`
  - `business_admin / admin`
- 代表性入口：
  - `action_project_material_plan`
  - `action_sc_tier_review_my_material_plan`
  - `action_payment_request_my`
  - `action_sc_tier_review_my_payment_request`
  - `action_project_budget`
  - `action_project_progress_entry`
- 代表性模型：
  - `project.material.plan`
  - `payment.request`
  - `project.budget`
  - `project.progress.entry`

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-472.yaml` → `PASS`
- read-only Odoo shell runtime audit on `sc_odoo` → completed

## Runtime facts

### 1. PM / `hujun`
- 角色面：
  - `sc_role_profile = pm`
  - `sc_role_effective = pm`
- 能力组：
  - `contract_manager = True`
  - `cost_user = True`
  - `cost_manager = False`
  - `material_manager = True`
  - `purchase_manager = True`
  - `finance_manager = False`
- 动作：
  - `material_plan = True`
  - `material_plan_review = True`
  - `payment_request_my = True`
  - `payment_request_review = False`
  - `project_budget = True`
  - `project_progress_entry = True`
- 模型权限：
  - `project.material.plan`: `create/write/read = True/True/True`
  - `payment.request`: `create/write/read = False/False/True`
  - `project.budget`: `create/write/read = False/False/True`
  - `project.progress.entry`: `create/write/read = True/True/True`

结论：
- `PM` 的项目口写/审路径已落到 `material_plan` 与 `progress_entry`
- `PM` 没有财务写权，也没有付款审批权
- 但 `payment_request_my` 入口仍可见，而模型无 `create/write`

### 2. Finance / `jiangyijiao`
- 角色面：
  - `sc_role_profile = finance`
  - `sc_role_effective = finance`
- 能力组：
  - `finance_manager = True`
  - `cost_user = False`
  - `cost_manager = False`
  - `material_manager = False`
  - `purchase_manager = False`
- 动作：
  - `material_plan = True`
  - `material_plan_review = False`
  - `payment_request_my = True`
  - `payment_request_review = True`
  - `project_budget = True`
  - `project_progress_entry = True`
- 模型权限：
  - `project.material.plan`: `create/write/read = False/False/True`
  - `payment.request`: `create/write/read = True/True/True`
  - `project.budget`: `create/write/read = False/False/True`
  - `project.progress.entry`: `create/write/read = False/False/False`

结论：
- `finance` 的财务写/审路径已正确落在 `payment.request`
- `finance` 没有物资审批，也没有项目进度写权
- 但 `project_progress_entry` 入口仍可见，而模型侧连 `read` 都没有

### 3. Executive / `wutao`
- 角色面：
  - `sc_role_profile = executive`
  - `sc_role_effective = executive`
- 动作全部 `True`
- 模型权限全部 `create/write/read = True/True/True`
- 能力组：
  - `contract_manager = True`
  - `cost_user = True`
  - `cost_manager = True`
  - `material_manager = True`
  - `purchase_manager = True`
  - `finance_manager = True`

结论：
- `executive` 的代表性写/审批路径已经完整落到业务 manager 面

### 4. Business Admin / `admin`
- 角色面：
  - `sc_role_profile = owner`
  - `sc_role_effective = pm`
- 动作全部 `True`
- 模型权限全部 `create/write/read = True/True/True`
- 能力组：
  - `business_full = True`
  - `contract_manager = True`
  - `cost_user = True`
  - `cost_manager = True`
  - `material_manager = True`
  - `purchase_manager = True`
  - `finance_manager = True`

结论：
- `business_admin` 的代表性写/审批路径已经完整落在 `group_sc_business_full`
- 但其展示语义仍不是独立主角色，`sc_role_effective = pm` 也说明当前角色展示层对 overlay authority 的表达仍有残差

## Repository cross-check
- [action_groups_patch.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/security/action_groups_patch.xml)
  - `action_sc_tier_review_my_payment_request` 被收口到 `group_sc_cap_finance_manager`
  - `action_sc_tier_review_my_material_plan` 被收口到 `group_sc_cap_material_manager`
  - `action_project_progress_entry` 被收口到 `group_sc_cap_cost_user/group_sc_cap_cost_manager`
- [ir.model.access.csv](/mnt/e/sc-backend-odoo/addons/smart_construction_core/security/ir.model.access.csv)
  - `project.progress.entry` 只有 `cost_user` 与 `cost_manager` 拥有写权
  - `project.budget` 的 `cost_read` 只有只读权
  - `project.material.plan` 只有 `material_user/material_manager` 拥有写权
  - `payment.request` 的写/审批归 `finance_user/finance_manager`
- 这与 runtime 结论大体一致：
  - 写权归属本身是对的
  - 但个别入口可见性仍比真实模型写权更宽

## Conclusion
- 代表性写路径归属已能清晰分类：
  - `PM`：项目口写/物资审批/进度录入
  - `finance`：付款申请写/付款审批
  - `executive`：全业务 manager
  - `business_admin`：`business_full` 全业务写/审
- 当前剩余问题不是主权限边界错配，而是入口可见性仍有两处残差：
  - `PM` 可见 `action_payment_request_my`，但无 `payment.request` 写权
  - `finance` 可见 `action_project_progress_entry`，但无 `project.progress.entry` 读写权

## Risk
- 结果：`PASS_WITH_RISK`
- 风险点：
  - “入口可见但模型无权”会造成页面进入后语义不稳定，属于典型交付面残差
  - `business_admin` 的 authority 已正确，但角色展示层仍无法稳定表达 overlay 语义

## Rollback
- `git restore agent_ops/tasks/ITER-2026-03-31-472.yaml`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-472.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-472.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 应停止连续推进，并新开一张窄治理/实现批次，只收口代表性入口与真实写权的一致性：
  - `PM -> payment_request_my`
  - `finance -> project_progress_entry`
