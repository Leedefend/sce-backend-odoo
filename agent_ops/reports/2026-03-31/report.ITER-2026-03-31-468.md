# ITER-2026-03-31-468

## Summary
- 对四川保盛首批关键流程做了更细的页面/动作链复审，聚焦 `PM` 与 `finance`
- 结论不是“全部完全一致”，而是 `PASS_WITH_RISK`
- `PM` 的关键流程页与动作链已经完整可用
- `finance` 的核心路径已经符合“财务专属 + 跨域只读”，但成本域内部仍有一个明确的读面不一致点：`预算/进度` 可进，`WBS` 不可进

## Scope
- 用户样本：
  - `hujun` (`pm`)
  - `jiangyijiao` (`finance`)
- 核查对象：
  - 菜单：
    - `menu_sc_contract_income`
    - `menu_sc_project_cost_ledger`
    - `menu_project_material_plan`
    - `menu_sc_tier_review_my_material_plan`
    - `menu_payment_request`
  - 动作：
    - `action_construction_contract_my`
    - `action_project_cost_ledger_my`
    - `action_project_material_plan`
    - `action_sc_tier_review_my_material_plan`
    - `action_payment_request_my`
    - `action_project_budget`
    - `action_project_wbs`
    - `action_project_progress_entry`

## Runtime facts

### PM / hujun
- 菜单：
  - 合同 `True`
  - 成本台账 `True`
  - 物资计划 `True`
  - 物资审批 `True`
  - 付款申请 `True`
- 动作：
  - 合同 `True`
  - 成本台账 `True`
  - 物资计划 `True`
  - 物资审批 `True`
  - 付款申请 `True`
  - 预算 `True`
  - WBS `True`
  - 进度 `True`

结论：
- `PM` 首批关键流程链已经成立

### Finance / jiangyijiao
- 菜单：
  - 合同 `True`
  - 成本台账 `True`
  - 物资计划 `True`
  - 物资审批 `False`
  - 付款申请 `True`
- 动作：
  - 合同 `True`
  - 成本台账 `True`
  - 物资计划 `True`
  - 物资审批 `False`
  - 付款申请 `True`
  - 预算 `True`
  - WBS `False`
  - 进度 `True`

结论：
- `finance` 的“财务专属 + 跨域只读”主链基本成立
- `物资审批` 为 `False` 是符合预期的，因为审批仍在 manager 路径
- 真正的差异点在成本域内部：
  - `预算` 可进
  - `进度` 可进
  - `WBS` 不可进

## Repository cross-check
- [action_groups_patch.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/security/action_groups_patch.xml)
  - `action_project_budget` 运行态组包含：
    - `group_sc_cap_cost_read`
    - `group_sc_cap_cost_user`
    - `group_sc_cap_cost_manager`
  - `action_project_progress_entry` 运行态组包含：
    - `group_sc_cap_cost_read`
    - `group_sc_cap_cost_user`
    - `group_sc_cap_cost_manager`
  - `action_project_wbs` 运行态组包含：
    - `group_sc_cap_cost_user`
    - `group_sc_cap_cost_manager`
    - `group_sc_cap_project_user`
    - `group_sc_cap_project_manager`
- 这解释了为什么 `finance` 作为 `cost_read` 用户：
  - 可以进入 `预算 / 进度`
  - 但仍无法进入 `WBS`

## Conclusion
- `PM`：首批关键页面与动作链可用
- `finance`：首批关键页面与动作链大体可用，但成本域的“只读面”尚未完全一致
- 当前最具体的读面缺口是：
  - `finance` 对成本域的 `WBS` 仍无只读入口

## Risk
- 结果：`PASS_WITH_RISK`
- 风险点：
  - 成本域读面不一致：`budget/progress` 向 `cost_read` 打开，`WBS` 仍未向 `cost_read` 打开
  - 这不阻断财务主链可用性，但会影响“所有业务域只读向内部用户打开”的一致性口径

## Rollback
- 本轮为只读复审，无实现代码变更需要回滚
- 如需撤回治理文件：
  - `git restore agent_ops/tasks/ITER-2026-03-31-468.yaml`
  - `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-468.md`
  - `git restore agent_ops/state/task_results/ITER-2026-03-31-468.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 若继续按交付口径收权限一致性，下一张最值当的是一个窄权限治理批次：
  - 决定 `WBS` 是否也应向 `cost_read` 打开只读入口
  - 若答案是应当打开，再做最小修补
