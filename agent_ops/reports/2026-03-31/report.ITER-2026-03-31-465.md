# ITER-2026-03-31-465

## Summary
- 对四川保盛首批业务流程做了只读运行态审计，聚焦 `PM / 财务 / 管理层 / 业务系统管理员`
- 结论不是“完全没问题”，而是 `PASS_WITH_RISK`
- `PM`、`管理层`、`业务系统管理员` 与当前升级后的权限口径基本对齐
- 但 `财务` 当前仍继承了 `owner` 路径下的项目口经办面，因此可见并可进入部分项目/合同/成本/物资/采购动作

## Scope
- 角色样本：
  - `hujun` (`pm`)
  - `jiangyijiao` (`finance`)
  - `wutao` (`executive`)
  - `duanyijun` (`executive + business_admin`)
- 入口集合：
  - 合同
  - 成本台账 / 预算 / WBS / 进度
  - 物资计划 / 物资审批
  - 付款申请

## Evidence

### Runtime flow surface
- `hujun / pm`
  - `menu_sc_contract_income` = allowed
  - `menu_sc_project_cost_ledger` = allowed
  - `menu_project_material_plan` = allowed
  - `menu_sc_tier_review_my_material_plan` = allowed
  - `action_construction_contract_my` = allowed
  - `action_project_cost_ledger_my` = allowed
  - `action_project_material_plan` = allowed
  - `action_sc_tier_review_my_material_plan` = allowed
  - `action_project_budget / action_project_wbs / action_project_progress_entry` = allowed
- `jiangyijiao / finance`
  - `menu_sc_contract_income` = allowed
  - `menu_sc_project_cost_ledger` = allowed
  - `menu_project_material_plan` = allowed
  - `menu_payment_request` = allowed
  - `menu_sc_tier_review_my_material_plan` = denied
  - `action_construction_contract_my` = allowed
  - `action_project_cost_ledger_my` = allowed
  - `action_project_material_plan` = allowed
  - `action_payment_request_my` = allowed
  - `action_project_budget / action_project_wbs / action_project_progress_entry` = allowed
- `wutao / executive`
  - 上述首批入口均为 allowed
- `duanyijun / executive + business_admin`
  - 上述首批入口均为 allowed

### Runtime authority facts
- `PM / hujun`
  - `contract_manager = True`
  - `cost_user = True`
  - `cost_manager = False`
  - `material_manager = True`
  - `purchase_manager = True`
  - `finance_user = False`
  - `finance_manager = False`
- `finance / jiangyijiao`
  - `contract_user = True`
  - `cost_user = True`
  - `material_user = True`
  - `purchase_user = True`
  - `finance_manager = True`
- `executive / wutao`
  - `cost_manager = True`
  - `material_manager = True`
  - `purchase_manager = True`
  - `finance_manager = True`
  - `base.group_system = False`
  - `group_sc_super_admin = False`
- `executive + business_admin / duanyijun`
  - `group_sc_business_full = True`
  - `finance_manager = True`
  - `base.group_system = False`

### Definition cross-check
- `payment_request_my` 在 [payment_request_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/core/payment_request_views.xml) 中仍只声明财务口：
  - `finance_read`
  - `finance_user`
  - `finance_manager`
- `cost_ledger_my` 在 [cost_domain_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/core/cost_domain_views.xml) 中是 `cost_read`
- 项目口增强后的 `PM` 权限与实际 `has_group()` 结果一致，没有财务泄漏

## Conclusion
- `PM`：首批项目口业务流程现在真实可用，且与“合同/物资/采购审批 + 成本经办”口径一致
- `管理层`：首批业务入口真实可用，且无平台级泄漏
- `业务系统管理员`：企业维护与业务全能力路径可用
- `财务`：当前不仅拥有财务口，还继承了项目口经办能力

## Risk
- 结果：`PASS_WITH_RISK`
- 风险点：
  - `finance` 角色仍沿 `owner` 路径获得项目/合同/成本/物资/采购经办面
  - 这在“系统可用性”上不是故障，但在“最终授权边界”上仍可能过宽
- 未发现：
  - `PM` 财务泄漏
  - `executive` 平台泄漏

## Rollback
- 本轮是只读审计，无产品代码变更需要回滚
- 如需撤回治理文件：
  - `git restore agent_ops/tasks/ITER-2026-03-31-465.yaml`
  - `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-465.md`
  - `git restore agent_ops/state/task_results/ITER-2026-03-31-465.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 若继续做四川保盛完整交付验证，建议先单开一张窄治理批次，只决定一件事：
  - `finance` 是否应继续继承项目口经办面
  - 还是把 `finance` 从 `owner` 路径中解耦，只保留财务口 + 必要跨域只读
