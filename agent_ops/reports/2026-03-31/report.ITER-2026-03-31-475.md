# ITER-2026-03-31-475

## Summary
- 审计了项目表单 `object button` 与其方法返回目标
- 结论为 `PASS_WITH_RISK`
- 发现新的 object-button 级 runtime 残差：部分按钮对交付角色可见，但方法执行时会撞到 `ir.actions.act_window.view` ACL

## Scope
- 本批仅做仓库与 runtime 审计
- 核查方法：
  - `action_open_cost_ledger`
  - `action_open_progress_entries`
  - `action_open_project_budgets`
  - `action_open_project_contracts`
  - `action_open_wbs`
  - `action_view_my_tasks`
  - `action_view_stage_requirements`
- 角色样本：
  - `PM / hujun`
  - `finance / jiangyijiao`
  - `executive / wutao`
  - `business_admin / admin`

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-475.yaml` → `PASS`
- repository/runtime audit on `sc_odoo` → `PASS_WITH_RISK`

## Repository facts
- [project_project_financial_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/core/project_project_financial_views.xml)
  - `action_open_project_budgets` 按钮对 `cost_user/cost_manager` 可见
  - `action_open_project_contracts` 按钮对 `contract_user/contract_manager` 可见
- [project_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/core/project_views.xml)
  - `action_open_cost_ledger` / `action_open_progress_entries` 对 `cost_user/cost_manager` 可见
  - `action_open_wbs` 对 `project_read` 可见
- [project_project_financial.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/core/project_project_financial.py)
  - `action_open_project_budgets/contracts` 通过 `env.ref(...).read()[0]` 构造返回 action
- [project_core.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/core/project_core.py)
  - `action_view_my_tasks` 通过 `env.ref(\"project.action_view_task\").read()[0]` 构造返回 action
  - `action_view_stage_requirements` 直接创建 wizard 记录

## Runtime facts
- 样本项目：
  - `project.id = 1`
  - `演示项目 · 立项待完善`

### 正常项
- `PM / hujun`
  - `action_open_cost_ledger` → `project.cost.ledger`，成功
  - `action_open_progress_entries` → `project.progress.entry`，成功
  - `action_open_wbs` → `construction.work.breakdown`，成功
- `finance / jiangyijiao`
  - `action_open_cost_ledger` / `action_open_progress_entries` / `action_open_wbs` 方法本身可返回 action，但这些按钮在视图层并不对财务开放
- `business_admin / admin`
  - `action_open_project_budgets` / `action_open_project_contracts` / `action_view_my_tasks` 均可成功返回目标 action

### 新发现的残差
- `PM / hujun`
  - `action_open_project_budgets` → `AccessError`
  - `action_open_project_contracts` → `AccessError`
  - `action_view_my_tasks` → `AccessError`
- `executive / wutao`
  - `action_open_project_budgets` → `AccessError`
  - `action_open_project_contracts` → `AccessError`
  - `action_view_my_tasks` → `AccessError`
- 错误统一落在：
  - `You are not allowed to access 'Action Window View' (ir.actions.act_window.view) records`

### 额外观察项
- `action_view_stage_requirements`
  - `PM / finance / executive / business_admin` 全部因
    `sc.project.stage.requirement.wizard` create ACL 缺失而失败
  - 这说明该 object button 当前更像未完成的治理入口，而不是已对齐的交付入口

## Conclusion
- 当前项目表单 object button 层并未完全对齐交付边界
- 新残差不是“按钮可见但 action groups 错了”，而是：
  - 按钮组看起来允许
  - 但方法内部通过 `env.ref(...).read()[0]` 读取 action 时碰到
    `ir.actions.act_window.view` ACL
- 因此这是比普通 action 可见性更深一层的方法执行残差，必须单开实现批次修复

## Risk
- 结果：`PASS_WITH_RISK`
- 风险点：
  - `PM` 与 `executive` 在项目表单上可能看到可点按钮，但点击后报 ACL 错误
  - `action_view_stage_requirements` 当前对交付角色整体不可用
  - 继续往下做业务流验收前，应先决定这些 object button 是要修通、隐藏，还是明确降级

## Rollback
- 本批为只读审计，无实现代码变更需要回滚
- 如需撤回治理文件：
  - `git restore agent_ops/tasks/ITER-2026-03-31-475.yaml`
  - `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-475.md`
  - `git restore agent_ops/state/task_results/ITER-2026-03-31-475.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 应新开一张窄实现批次，专门收口项目表单 object button 方法：
  - `action_open_project_budgets`
  - `action_open_project_contracts`
  - `action_view_my_tasks`
  - 视情况一并决定 `action_view_stage_requirements` 的交付策略
