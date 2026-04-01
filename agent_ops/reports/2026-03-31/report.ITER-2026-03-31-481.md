# ITER-2026-03-31-481

## Summary
- 审计了 representative next-action 从 recommendation 到 execution 的端到端一致性
- 结论为 `PASS_WITH_RISK`
- 发现新的 recommendation-layer 残差：`sc_next_action_submit_project` 的 `condition_expr` 在 runtime `safe_eval` 时因缩进格式失败

## Scope
- 本批仅做仓库与 runtime 审计
- 关注对象：
  - `project_next_action_rules.xml`
  - `sc.project.next_action.service.get_next_actions()`
  - `project.project.sc_execute_next_action()`
- 角色样本：
  - `PM / hujun`
  - `executive / wutao`
  - `business_admin / admin`
- 项目样本：
  - `draft / project.id = 1`
  - `in_progress / project.id = 15`

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-481.yaml` → `PASS`
- repository/runtime audit on `sc_odoo` → `PASS_WITH_RISK`

## Repository facts
- [project_next_action_rules.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/data/project_next_action_rules.xml#L4)
  - `sc_next_action_submit_project` 的 `condition_expr` 是多行缩进文本
- [project_next_action_service.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/services/project_next_action_service.py#L32)
  - `get_next_actions()` 直接把 `rule.condition_expr` 送进 `safe_eval`
  - 当前没有对多行 XML 缩进表达式做预清洗

## Runtime facts
- `draft / project.id = 1`
  - `PM / executive / business_admin` 都拿到：
    - `创建合同` → 执行成功 → `construction.contract`
  - 但 runtime 日志对 `sc_next_action_submit_project` 连续报：
    - `[sc_next_action] rule=1 eval failed: unexpected indent (, line 2)`
- `in_progress / project.id = 15`
  - `PM / executive / business_admin` 都拿到：
    - `维护成本台账` → 执行成功 → `project.cost.ledger`
    - `创建任务` → 执行成功 → `project.task`
- 本批已命中的 representative recommendation-execution pair 没有发现新的 dispatcher 残差

## Conclusion
- recommendation/execution 基线在已命中的 representative 路径上总体已对齐
- 但 `draft` 阶段最前面的“提交立项”规则本身因为表达式缩进问题没有被正常评估
- 这不是 ACL/dispatcher 问题，而是 next-action rule 表达式规范化问题

## Risk
- 结果：`PASS_WITH_RISK`
- 风险点：
  - `draft` 阶段可能漏掉应出现的“提交立项”推荐
  - 只要 `condition_expr` 仍以当前缩进形式进入 `safe_eval`，就会持续产生 recommendation 层漏判

## Rollback
- 本批为只读审计，无实现代码变更需要回滚
- 如需撤回治理文件：
  - `git restore agent_ops/tasks/ITER-2026-03-31-481.yaml`
  - `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-481.md`
  - `git restore agent_ops/state/task_results/ITER-2026-03-31-481.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 需要新开一张窄实现批次，专门修 next-action rule expression 的规范化：
  - 要么在服务层对 `condition_expr` 做缩进清洗
  - 要么把受影响规则改成单行/无歧义表达式
