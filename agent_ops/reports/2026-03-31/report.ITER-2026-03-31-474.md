# ITER-2026-03-31-474

## Summary
- 对四川保盛首批主流程之外的细粒度按钮、quick action 和备用入口做了只读复审
- 结果为 `PASS`
- 在 `473` 修正后的基线上，本轮未发现新的“写入口越权可见”残差

## Scope
- 本批仅做仓库与 runtime 审计
- 角色样本：
  - `PM / hujun`
  - `finance / jiangyijiao`
  - `executive / wutao`
  - `business_admin / admin`
- 入口集合：
  - `action_payment_request_my`
  - `action_project_budget_quick`
  - `action_project_cost_ledger_quick`
  - `action_project_progress_quick`
  - `action_project_contract_overview`
  - `action_project_budget`
  - `action_construction_contract`

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-474.yaml` → `PASS`
- repository/runtime audit on `sc_odoo` → `PASS`

## Runtime facts

### PM / `hujun`
- quick/button entries:
  - `payment_request_my = False`
  - `project_budget_quick = True`
  - `project_cost_ledger_quick = True`
  - `project_progress_quick = True`
  - `project_contract_overview = True`
- model write rights:
  - `payment_request = False`
  - `project_budget = False`
  - `project_cost_ledger = True`
  - `project_progress_entry = True`
  - `construction_contract = True`

结论：
- `PM` 已不再暴露财务写入口
- `budget_quick` 虽可见，但对应的是已冻结的成本只读面，不构成新的写权残差

### Finance / `jiangyijiao`
- quick/button entries:
  - `payment_request_my = True`
  - `project_budget_quick = False`
  - `project_cost_ledger_quick = False`
  - `project_progress_quick = False`
  - `project_contract_overview = False`
  - `project_budget = True`
  - `construction_contract = True`
- model write rights:
  - `payment_request = True`
  - `project_budget = False`
  - `project_cost_ledger = False`
  - `project_progress_entry = False`
  - `construction_contract = False`

结论：
- `finance` 的 quick 写入口已经收紧到财务口
- 仍可进入 `project_budget` / `construction_contract` 的 canonical action，但这与前面已冻结的跨域只读口径一致，不是新出现的 button residual

### Executive / `wutao`
- 所有细粒度入口均为 `True`
- 所有对应模型写权均为 `True`

### Business Admin / `admin`
- 所有细粒度入口均为 `True`
- 所有对应模型写权均为 `True`

## Repository cross-check
- [project_overview_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/core/project_overview_views.xml)
  - 财务卡片直接复用 `action_payment_request_my`
  - 因此 `473` 对该 action 的收窄已经同步修复 overview 入口
- [project_project_financial_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/core/project_project_financial_views.xml)
  - 项目表单头部 `预算/合同` 按钮仍显式绑定到 `cost_user/cost_manager` 与 `contract_user/contract_manager`
- [project_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/core/project_views.xml)
  - quick actions 继续走 `cost_user/cost_manager` 与 `contract_user/contract_manager`，没有重新把 `finance_read` 或 `cost_read` 带回写入口

## Conclusion
- 在 `473` 修正后的基线上，本轮审计未发现新的细粒度写入口残差
- 当前还存在的“可见但无写权”现象都落在已冻结的 canonical 只读入口上：
  - `finance -> project_budget / construction_contract`
  - `PM -> project_budget`
- 这些属于既有交付口径中的读面，不是 quick/button 层新增的越权入口

## Risk
- 结果：`PASS`
- 观察项：
  - canonical 读入口与 quick 写入口的语义分层仍需团队继续保持，不要后续混回同一 action
  - `business_admin` 展示语义残差仍独立存在，但不属于本批按钮/入口审计范围

## Rollback
- 本批为只读审计，无实现代码变更需要回滚
- 如需撤回治理文件：
  - `git restore agent_ops/tasks/ITER-2026-03-31-474.yaml`
  - `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-474.md`
  - `git restore agent_ops/state/task_results/ITER-2026-03-31-474.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 可继续扩到非首批流程或非代表性 object button，或者回到产品侧决定是否要把 canonical 读入口和 quick 写入口做更显式的 UI 语义区分
