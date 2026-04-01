# ITER-2026-03-31-484

## Summary
- 审计了 `overview -> next_action` 管线里的 `cost.count` 错配来源
- 结论为 `PASS_WITH_RISK`
- 根因已经收缩到 [project_overview_service.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/services/project_overview_service.py)：服务读取 `read_group` 结果时用了错误的计数字段名

## Scope
- 本批仅做仓库与 runtime 审计
- 关注对象：
  - `sc.project.overview.service.get_overview()`
  - `project.cost.ledger.read_group(...)`
  - next-action 对 `s['cost']['count']` 的消费
- 角色样本：
  - `PM / hujun`
  - `executive / wutao`
  - `business_admin / admin`
- 项目样本：
  - `in_progress / project.id = 20`

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-484.yaml` → `PASS`
- repository/runtime audit on `sc_odoo` → `PASS_WITH_RISK`

## Repository facts
- [project_overview_service.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/services/project_overview_service.py#L42)
  - `project.cost.ledger.read_group()` 之后，当前写法是：
    - `data[project_id]["cost"]["count"] = rec.get("__count", 0)`
- 但 `read_group([\"project_id\"], [\"project_id\"])` 的结果并不保证返回 `__count`

## Runtime facts
- `project.id = 20`
  - 对 `PM / executive / business_admin`
    - `project.cost.ledger.search_count([('project_id', '=', 20)])` → `4`
    - `sc.project.overview.service.get_overview([20])[20]['cost']['count']` → `0`
    - `_can_read_model('project.cost.ledger')` → `True`
- 同一批次直接执行：
  - `project.cost.ledger.read_group([('project_id', 'in', [20])], ['project_id'], ['project_id'])`
  - 返回的是：
    - `project_id_count = 4`
  - 而不是 `__count`

## Conclusion
- `483` 的 recommendation correctness 残差不是规则条件错，也不是 ACL 导致
- 根因是 overview 聚合服务读取 `read_group` 结果时使用了错误的 count key
- 因此下一步不需要改权限或规则，只需要开一张窄实现批次修正聚合服务的 count 读取逻辑

## Risk
- 结果：`PASS_WITH_RISK`
- 风险点：
  - 只要 `cost.count` 继续被写成 `0`，`维护成本台账` recommendation 就会在已有成本项目上持续误报
  - 同类 `read_group` 读取如果其他分支也用了 `__count`，可能存在相同形态的潜在偏差

## Rollback
- 本批为只读审计，无实现代码变更需要回滚
- 如需撤回治理文件：
  - `git restore agent_ops/tasks/ITER-2026-03-31-484.yaml`
  - `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-484.md`
  - `git restore agent_ops/state/task_results/ITER-2026-03-31-484.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 需要新开一张窄实现批次，修 `sc.project.overview.service` 对 `read_group` count 字段的读取，并回归验证 `cost.count` 与 recommendation 输出同步恢复
