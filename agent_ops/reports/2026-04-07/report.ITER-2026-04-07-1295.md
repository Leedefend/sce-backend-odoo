# ITER-2026-04-07-1295 Report

## Summary of change
- 仅执行“outsider 样本语义统一”专题，不扩展新业务面。
- 修改 `scripts/verify/native_business_fact_fresh_install_min_flow_verify.py`：
  - 默认不再使用 `outsider_seed`。
  - 改为运行期创建临时最小权限 outsider（仅 `base.group_user`），验证后自动清理。
  - outsider 对 `project/task/budget/cost` 校验升级为严格 `count=0`（或 ACL 拒绝视为不可见）。
  - 增加 PM 登录失败回退（core-only fresh 场景使用 owner 作为 PM）。

## Batch A: outsider_seed 语义审计
- 审计库：`sc_prod_fresh_1292_b`
- 账号：`outsider_seed`
- 关键发现：
  - 含 `project.group_project_user`
  - 含 `smart_construction_core.group_sc_cap_project_read`
  - 含 `smart_construction_core.group_sc_cap_project_user`
- 结论：`outsider_seed` 不是“纯 outsider”，会天然带来 project/task 可见性噪音。

## Verification result
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-07-1295.yaml`
- PASS: `DB_NAME=sc_prod_fresh_1292_b ... python3 scripts/verify/native_business_fact_fresh_install_min_flow_verify.py`
  - `outsider_project_count=0 outsider_task_count=0 outsider_budget_count=0 outsider_cost_count=0`
- PASS: `DB_NAME=sc_prod_fresh_1292_b ... python3 scripts/verify/native_business_fact_non_member_denial_verify.py`
- PASS: `DB_NAME=sc_prod_fresh_core_1293 ... python3 scripts/verify/native_business_fact_fresh_install_min_flow_verify.py`
  - `outsider_project_count=0 outsider_task_count=0 outsider_budget_count=0 outsider_cost_count=0`
- PASS: `DB_NAME=sc_prod_fresh_core_1293 ... python3 scripts/verify/native_business_fact_non_member_denial_verify.py`

## Batch B: conclusion freeze
- 更新文档：
  - `docs/ops/project_org_isolation_acceptance_v1.md`
  - `docs/ops/project_org_isolation_design_v1.md`
- 冻结结论：
  - `project/task/budget/cost/payment/settlement` 进入“非成员默认拒绝”结论。
  - 明确特权放行边界与正式验证脚本清单。

## Risk analysis
- 结论：`PASS`
- 风险状态：上一轮 outsider 样本语义噪音已收敛，当前无新增阻塞风险。

## Rollback suggestion
- `git restore scripts/verify/native_business_fact_fresh_install_min_flow_verify.py`
- `git restore docs/ops/project_org_isolation_acceptance_v1.md`
- `git restore docs/ops/project_org_isolation_design_v1.md`

## Next suggestion
- 进入下一专项前，保持本轮脚本口径不变，仅在新主题下增量扩展验证范围。
