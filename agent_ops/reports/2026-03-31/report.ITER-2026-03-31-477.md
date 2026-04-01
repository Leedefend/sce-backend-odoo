# ITER-2026-03-31-477

## Summary
- 基于 `476` 修正后的基线，继续审计了 secondary navigation / follow-through 入口
- 结论为 `PASS_WITH_RISK`
- 发现新的二跳残差：overview 按钮虽然已隐藏，但 `sc_get_next_actions()` 仍向交付角色下发 `action_view_stage_requirements` 作为 fallback

## Scope
- 本批仅做仓库与 runtime 审计
- 关注对象：
  - project overview 的 next-action/fallback 下发
  - 与 `action_view_stage_requirements` 相关的二跳入口
- 角色样本：
  - `PM / hujun`
  - `executive / wutao`
  - `business_admin / admin`

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-477.yaml` → `PASS`
- repository/runtime audit on `sc_odoo` → `PASS_WITH_RISK`

## Repository facts
- [project_core.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/core/project_core.py#L1510)
  - `sc_get_next_actions()` 在 `actions` 之外固定下发：
    - `fallback.title = 查看阶段要求`
    - `fallback.action_type = object_method`
    - `fallback.action_ref = action_view_stage_requirements`
- 这条 fallback 与 [project_overview_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/core/project_overview_views.xml#L45) 中已被隐藏的 overview 按钮不一致

## Runtime facts
- 样本项目：
  - `project.id = 16`
- `PM / hujun`
  - `sc_get_next_actions(limit=3)` → `fallback.action_ref = action_view_stage_requirements`
- `executive / wutao`
  - `sc_get_next_actions(limit=3)` → `fallback.action_ref = action_view_stage_requirements`
- `business_admin / admin`
  - `sc_get_next_actions(limit=3)` → `fallback.action_ref = action_view_stage_requirements`
- 三个角色的 `actions` 列表均为空，但 fallback 仍然稳定存在

## Conclusion
- `476` 只收口了 overview button 层，没有同时收口 next-action/fallback 下发层
- 因此“阶段要求入口不再暴露”目前只在静态视图层成立，不在 secondary navigation 层成立
- 这是新的真实残差，不适合继续向更深业务流验收推进

## Risk
- 结果：`PASS_WITH_RISK`
- 风险点：
  - 若前端消费 `fallback`，交付角色仍可能通过 next-action 通路重新进入 `action_view_stage_requirements`
  - 当前 UI 和 next-action 契约语义不一致，容易造成“主入口隐藏，但推荐入口仍暴露”的行为分裂

## Rollback
- 本批为只读审计，无实现代码变更需要回滚
- 如需撤回治理文件：
  - `git restore agent_ops/tasks/ITER-2026-03-31-477.yaml`
  - `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-477.md`
  - `git restore agent_ops/state/task_results/ITER-2026-03-31-477.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 需要新开一张窄实现批次，专门处理 `sc_get_next_actions()` 的 fallback 语义：
  - 要么对 delivered roles 移除 `action_view_stage_requirements`
  - 要么显式把 fallback 改成与当前 overview 可见性一致的安全入口
