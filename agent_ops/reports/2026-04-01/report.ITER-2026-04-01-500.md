# ITER-2026-04-01-500

## Summary
- 继续审计第二个非首批代表家族：`BOQ import / task-from-BOQ / execution-structure / progress-entry`
- 结论为 `PASS_WITH_RISK`
- 发现新的真实 runtime 残差：代表性执行侧入口虽然按 groups 可见，但实际执行统一撞上 `ir.actions.act_window.view` ACL

## Scope
- 本批仅做仓库与 runtime 审计
- 角色样本：
  - `PM / hujun`
  - `finance / jiangyijiao`
  - `executive / wutao`
  - `business_admin / admin`
- 入口集合：
  - `action_project_boq_import_wizard`
  - `action_project_task_from_boq_wizard`
  - `action_exec_structure_entry`
  - `action_exec_structure_wbs`
  - `action_project_progress_entry`

## Repository facts
- [action_groups_patch.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/security/action_groups_patch.xml)
  - `action_project_boq_import_wizard` / `action_project_task_from_boq_wizard` / `action_project_progress_entry`
    都被收敛到 `cost_user/cost_manager`
  - `action_exec_structure_entry` / `action_exec_structure_wbs`
    仍面向 `project_read`
- [project_boq_import_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/core/project_boq_import_views.xml)
  - BOQ 导入是 wizard 入口
- [project_task_from_boq_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/core/project_task_from_boq_views.xml)
  - 从清单生成任务是 wizard 入口
- [execution_structure_actions_base.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/actions/execution_structure_actions_base.xml)
  - `action_exec_structure_entry` 为 server action，会在项目唯一时直接跳到 `action_exec_structure_wbs`
- [cost_domain_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/core/cost_domain_views.xml)
  - `action_project_progress_entry` 原始定义仍引用 act_window 视图链

## Runtime facts
- 入口可见性与模型权限：
  - `PM / executive / business_admin`
    - `project_boq_import_wizard = visible`
    - `project_task_from_boq_wizard = visible`
    - `exec_structure_entry = visible`
    - `project_progress_entry = visible`
  - `finance`
    - `project_boq_import_wizard = hidden`
    - `project_task_from_boq_wizard = hidden`
    - `project_progress_entry = hidden`
    - `exec_structure_entry = visible`
- 模型权限面：
  - `PM / executive / business_admin` 对相关 wizard / WBS / progress 模型均有 `read/write/create`
  - `finance` 对 `construction.work.breakdown` 仅只读，其余相关模型无写权
- 代表性 no-write runtime 执行：
  - `project.action_open_project_progress_entry()`
  - `action_exec_structure_entry.run()`
  对 `PM / finance / executive` 全部稳定报：
  - `AccessError: ir.actions.act_window.view`

## Conclusion
- 这批发现的是新的真实执行侧 residual，不是样本不足：
  - groups 可见性和模型 ACL 看起来允许
  - 但入口 follow-through 仍依赖 `ir.actions.act_window.view` 读取
  - delivered roles 在 runtime 上无法真正进入这些 secondary execution entrypoints
- 因此第二个非首批家族当前不能判为 clean PASS

## Risk
- 结果：`PASS_WITH_RISK`
- 风险点：
  - 这不是审计口径问题，而是实际入口执行失败
  - 下一步若继续，必须新开一张窄实现批次，只修这些 execution-side action 的 `ir.actions.act_window.view` 依赖路径

## Rollback
- 本批为审计批次，无仓库实现改动需要回滚
- 如需撤回治理文件：
  - `git restore agent_ops/tasks/ITER-2026-04-01-500.yaml`
  - `git restore agent_ops/reports/2026-04-01/report.ITER-2026-04-01-500.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-01-500.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 不能继续自动扩面
- 需要新开一张窄实现批次，只修：
  - `action_open_project_progress_entry`
  - `action_exec_structure_entry` follow-through
  - 以及相关 act_window 读取分支，避免 delivered roles 再撞 `ir.actions.act_window.view` ACL
