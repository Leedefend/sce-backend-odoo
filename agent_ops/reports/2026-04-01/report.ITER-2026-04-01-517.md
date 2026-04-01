# ITER-2026-04-01-517

## Summary
- 选定并审计了 `project dashboard / operating metrics` 家族
- 结论为 `PASS`
- 当前驾驶舱与经营指标家族可以并入 clean representative non-first-batch family 集合

## Scope
- 本批为 audit-first family selection
- 代表入口：
  - [project_dashboard_kanban.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/projection/project_dashboard_kanban.xml)
    的 `action_project_dashboard`
  - [operating_metrics_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/projection/operating_metrics_views.xml)
    的 `action_sc_operating_metrics_project`
- 角色样本：
  - `PM / hujun`
  - `finance / jiangyijiao`
  - `executive / wutao`
  - `business_admin / admin`

## Repository facts
- [project_dashboard_kanban.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/projection/project_dashboard_kanban.xml)
  定义 `action_project_dashboard -> project.project`
- [operating_metrics_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/projection/operating_metrics_views.xml)
  定义 `action_sc_operating_metrics_project -> sc.operating.metrics.project`
- [action_groups_patch.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/security/action_groups_patch.xml)
  对这两条 action 的 groups 进行了显式收敛：
  - `action_project_dashboard` → `project_read`
  - `action_sc_operating_metrics_project` → `project_read / cost_read / finance_read`
- [ir.model.access.csv](/mnt/e/sc-backend-odoo/addons/smart_construction_core/security/ir.model.access.csv)
  对模型的 ACL 也保持一致：
  - `project.project`：标准项目读写梯度
  - `sc.operating.metrics.project`：只读梯度

## Runtime facts
- 四个样本角色下：
  - `menu_sc_project_dashboard` 均可见
  - `menu_sc_operating_metrics_project` 均可见
  - `action_project_dashboard` 可正常读取，`res_model = project.project`
  - `action_sc_operating_metrics_project` 可正常读取，`res_model = sc.operating.metrics.project`
- 当前 `sc_odoo` runtime 上：
  - `project.project`
    - `PM / executive / business_admin`：可写
    - `finance`：只读
  - `sc.operating.metrics.project`
    - 四个样本角色全部为只读

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-517.yaml` → `PASS`
- repository audit → `PASS`
- runtime audit on `sc_odoo` → `PASS`

## Conclusion
- `project dashboard / operating metrics` 当前可以作为新的 clean representative non-first-batch family
- 当前没有发现菜单、action 与目标模型之间的 runtime residual
- 本批未展开 `settlement / payment risk` drill-down 按钮执行路径；但 canonical family surface 本身是干净的

## Risk
- 结果：`PASS`
- 剩余风险：
  - 本批只审计 canonical dashboard/metrics surface
  - 经营指标里的 financial drill-down 执行细节仍可另开更细批次；当前没有新的阻断 residual

## Rollback
- 本批为审计批次，无业务代码需要回滚
- 如需撤回治理文件：
  - `git restore agent_ops/tasks/ITER-2026-04-01-517.yaml`
  - `git restore agent_ops/reports/2026-04-01/report.ITER-2026-04-01-517.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-01-517.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 继续自动推进
- 新开下一张低风险筛选批次，继续选择尚未覆盖的 non-first-batch family
