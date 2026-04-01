# ITER-2026-04-01-508

## Summary
- 执行了 `tender` 有效权限泄漏诊断批次
- 结论为 `PASS`
- 根因已经确认：`507` 的 runtime fail 主要来自样本用户构造污染，而不是 tender 读写拆分方案本身失效

## Scope
- 本批为 audit-only diagnosis
- 未继续修改 ACL、action 或 view 实现

## Diagnosis facts
- [res_users_role_profile.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/support/res_users_role_profile.py)
  中 `res.users.create()` 会把 `sc_role_profile` 默认归一为 `owner`，随后执行
  `_sync_sc_role_profile_groups()`
- 这意味着只要用普通 `res.users.create()` 新建样本用户，即便只传
  `group_sc_cap_project_read`，也会自动被挂上 `owner` 相关 role overlay
- 用全新 login 的 runtime 诊断样本复核后，`project_read` 样本用户的实际 groups
  确认包含：
  - `smart_construction_custom.group_sc_role_owner`
  - `smart_construction_custom.group_sc_role_project_user`
  - `smart_construction_core.group_sc_cap_project_user`
  - 以及 owner 带出的其他业务能力组
- 所以前一轮看到的 `tender create/write = True` 不是
  `group_sc_cap_project_read` 自己 implied 出写权，而是样本用户在创建时已经被
  owner overlay 污染

## Runtime facts
- 用真实 runtime 角色复核 `sc_odoo` 后：
  - `finance / jiangyijiao`
    - `tender read = True`
    - `create/write/unlink = False`
    - form 上 `clickable_count = 0`, `readonly_count = 1`
  - `pm / hujun`
    - `tender read/create/write/unlink = True`
    - form 上 `clickable_count = 1`, `readonly_count = 0`
  - `executive / wutao`
    - `tender read/create/write/unlink = True`
    - form 上 `clickable_count = 1`, `readonly_count = 0`
- 这说明 `507` 的 tender 查询面 / 执行面实现，在真实交付角色上是符合目标语义的

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-508.yaml` → `PASS`
- runtime diagnosis on fresh users and real delivered roles → `PASS`

## Conclusion
- `507` 暴露的“写权泄漏”不是最终 runtime 业务残差，而是测试/诊断样本构造问题
- 当前真正需要补的不是第二轮 ACL 改动，而是：
  - tender 回归样本必须改成真实业务角色验证
  - 不能再用默认 `owner` overlay 污染的 group-only 新建用户来判 tender 读写边界

## Risk
- 结果：`PASS`
- 剩余风险：
  - 当前仓库里的 tender 回归样本仍不稳，如果继续沿用旧样本方式，会重复报假失败
  - 下一步应开一张更窄批次，只修 tender 验证样本与断言口径

## Rollback
- 本批为诊断批次，无业务代码需要回滚
- 如需撤回治理文件：
  - `git restore agent_ops/tasks/ITER-2026-04-01-508.yaml`
  - `git restore agent_ops/reports/2026-04-01/report.ITER-2026-04-01-508.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-01-508.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 继续自动推进
- 新开一张超窄批次，只修 tender 回归验证样本与断言，改成真实 runtime 角色语义
