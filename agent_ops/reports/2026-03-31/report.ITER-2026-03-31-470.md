# ITER-2026-03-31-470

## Summary
- 对四川保盛 `executive` 与 `business_admin` 做了首批关键流程的具体页面/动作链验收
- 结果为 `PASS`
- 当前剩余问题不是运行态权限残差，而是 `business_admin` 的展示语义仍显示为 `owner`

## Scope
- 本批仅做只读 runtime / config audit
- 变更路径：
  - [report.ITER-2026-03-31-470.md](/mnt/e/sc-backend-odoo/agent_ops/reports/2026-03-31/report.ITER-2026-03-31-470.md)
  - [ITER-2026-03-31-470.json](/mnt/e/sc-backend-odoo/agent_ops/state/task_results/ITER-2026-03-31-470.json)
  - [delivery_context_switch_log_v1.md](/mnt/e/sc-backend-odoo/docs/ops/iterations/delivery_context_switch_log_v1.md)
- 不涉及：
  - `addons/**`
  - ACL / record rules
  - payment / settlement / account 语义

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-470.yaml` → `PASS`
- runtime/config audit on `sc_odoo` → `PASS`

### Runtime audit facts

#### 1. Executive
- 用户：`wutao`
- 菜单全部可用：
  - `menu_sc_contract_income = True`
  - `menu_sc_project_cost_ledger = True`
  - `menu_sc_project_wbs_cost = True`
  - `menu_project_material_plan = True`
  - `menu_sc_tier_review_my_material_plan = True`
  - `menu_payment_request = True`
- 动作全部可用：
  - `action_construction_contract_my = True`
  - `action_project_cost_ledger_my = True`
  - `action_project_wbs = True`
  - `action_project_material_plan = True`
  - `action_sc_tier_review_my_material_plan = True`
  - `action_payment_request_my = True`
  - `action_project_budget = True`
  - `action_project_progress_entry = True`
- 业务 manager 权限已到位：
  - `contract_manager = True`
  - `cost_manager = True`
  - `material_manager = True`
  - `purchase_manager = True`
  - `finance_manager = True`
- 平台泄漏为 `0`：
  - `base.group_system = False`
  - `group_sc_super_admin = False`

#### 2. Business Admin
- 用户：`admin`
- 菜单全部可用：
  - `menu_sc_contract_income = True`
  - `menu_sc_project_cost_ledger = True`
  - `menu_sc_project_wbs_cost = True`
  - `menu_project_material_plan = True`
  - `menu_sc_tier_review_my_material_plan = True`
  - `menu_payment_request = True`
- 动作全部可用：
  - `action_construction_contract_my = True`
  - `action_project_cost_ledger_my = True`
  - `action_project_wbs = True`
  - `action_project_material_plan = True`
  - `action_sc_tier_review_my_material_plan = True`
  - `action_payment_request_my = True`
  - `action_project_budget = True`
  - `action_project_progress_entry = True`
- 运行态 authority 正常：
  - `group_sc_business_full = True`
  - `contract_manager = True`
  - `cost_manager = True`
  - `material_manager = True`
  - `purchase_manager = True`
  - `finance_manager = True`

## Conclusion
- 四川保盛 `executive` 的首批关键页面与动作链已经真实可用
- `executive` 具备完整业务域 manager 权限，但没有平台级权限泄漏
- 四川保盛 `business_admin` 的首批关键页面与动作链也已经真实可用
- 当前唯一残留是 `admin.sc_role_profile` 展示仍为 `owner`，但这不影响运行态 business-admin authority

## Risk
- 结果：`PASS`
- 观察项：
  - `business_admin` 的展示语义与运行态 authority 仍未完全对齐
  - 该残差不会影响具体页面/动作链可用性，但会影响角色标签解释一致性

## Rollback
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-470.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-470.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 首批角色流程验收链已覆盖：
  - `PM`
  - `finance`
  - `executive`
  - `business_admin`
- 当前最合理的下一步是开一张窄治理批次，把 `business_admin` 的展示语义与运行态 authority 对齐
