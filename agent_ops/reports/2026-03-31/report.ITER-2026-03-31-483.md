# ITER-2026-03-31-483

## Summary
- 审计了 role-specific next-action recommendation 稳定性
- 结论为 `PASS_WITH_RISK`
- 发现新的 recommendation-layer 残差：`in_progress` 样本项目即使已有成本台账，仍持续收到 `维护成本台账`

## Scope
- 本批仅做仓库与 runtime 审计
- 关注对象：
  - `sc.project.next_action.service.get_next_actions()`
  - role-specific recommendation stability
- 角色样本：
  - `PM / hujun`
  - `executive / wutao`
  - `business_admin / admin`
- 项目样本：
  - `draft / project.id = 1`
  - `in_progress_cost_gap / project.id = 15`
  - `in_progress_has_cost / project.id = 20`

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-483.yaml` → `PASS`
- repository/runtime audit on `sc_odoo` → `PASS_WITH_RISK`

## Repository facts
- [project_next_action_rules.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/data/project_next_action_rules.xml#L54)
  - `sc_next_action_update_cost` 的条件是：
    - `s.get('cost', {}).get('count', 0) == 0`
- 按规则语义，已有成本台账的 in-progress 项目不应继续收到这条 recommendation

## Runtime facts
- `draft / project.id = 1`
  - `PM / executive / business_admin` 拿到完全一致的 recommendation：
    - `提交立项`
    - `创建合同`
- `in_progress_cost_gap / project.id = 15`
  - 三种角色拿到完全一致的 recommendation：
    - `维护成本台账`
    - `创建任务`
- `in_progress_has_cost / project.id = 20`
  - 该项目在先前仓库/runtime 摸底里 `cost_count = 4`
  - 但三种角色仍然都拿到：
    - `维护成本台账`
    - `创建任务`
- 这说明当前 recommendation 输出在 role 之间是稳定的，但和项目事实不一致

## Conclusion
- `483` 没有发现新的 role-specific 分叉问题
- 但发现了更基础的 recommendation correctness 残差：
  - 成本台账规则命中结果与项目实际 `cost_count` 不一致
- 因此当前 next-action 基线还不能宣称完全稳定

## Risk
- 结果：`PASS_WITH_RISK`
- 风险点：
  - in-progress 项目即使已有成本数据，仍可能被错误推荐去“维护成本台账”
  - 这会让 recommendation 层语义偏离真实项目状态，降低 next-action 的可信度

## Rollback
- 本批为只读审计，无实现代码变更需要回滚
- 如需撤回治理文件：
  - `git restore agent_ops/tasks/ITER-2026-03-31-483.yaml`
  - `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-483.md`
  - `git restore agent_ops/state/task_results/ITER-2026-03-31-483.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 需要新开一张窄审计或实现批次，先确认 `overview service / stats` 中的 `cost.count` 口径为什么与项目 20 的 runtime 事实不一致，再决定修规则还是修统计来源
