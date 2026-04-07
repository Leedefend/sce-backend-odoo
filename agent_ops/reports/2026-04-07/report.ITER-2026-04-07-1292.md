# ITER-2026-04-07-1292 Report

## Summary of execution
- 执行 fresh-runtime 连续防再生 v1（Batch A/B/C）：
  1) 多库抽样：`sc_prod_fresh_1292_a`、`sc_prod_fresh_1292_b`
  2) install-order 守卫常态化：新增 guard verify + 最小规则文档
  3) fresh 最小业务流防再生：项目→成员→任务→预算→成本，并校验锚点与角色可见性

## Batch B (guard) result
- 新增：`scripts/verify/native_business_fact_install_order_guard_verify.py`
- 新增：`docs/ops/install_order_guard_min_rules_v1.md`
- PASS: `python3 scripts/verify/native_business_fact_install_order_guard_verify.py`

## Batch C (fresh minimal flow) result
- 新增：`scripts/verify/native_business_fact_fresh_install_min_flow_verify.py`
- 在 fresh 库创建并验证：
  - `project.project`（含关键岗位字段）
  - `project.responsibility`（项目成员）
  - `project.task`
  - `project.budget`
  - `project.cost.ledger`
- 锚点结果：预算/成本 `project_id`、`company_id` 与项目锚点一致（PASS）。
- 角色结果：PM 对新建项目/任务/预算/成本可见（PASS）；outsider 对预算/成本不可见（PASS）。
- 观测项：outsider 对项目/任务可见（observed，不作为本轮阻断项，已记录差异）。

## Batch A (multi-fresh sampling) matrix
- Sample A (`sc_prod_fresh_1292_a`)
  - `mod.install smart_construction_custom`: PASS
  - `mod.install smart_construction_scene`: PASS
  - `native_business_fact_budget_cost_member_visibility_verify`: PASS
  - `native_business_fact_fresh_install_min_flow_verify`: PASS
  - `verify.native.business_fact.stage_gate`: PASS
- Sample B (`sc_prod_fresh_1292_b`)
  - `mod.install smart_construction_custom`: PASS
  - `mod.install smart_construction_scene`: PASS
  - `native_business_fact_budget_cost_member_visibility_verify`: PASS
  - `native_business_fact_fresh_install_min_flow_verify`: PASS
  - `verify.native.business_fact.stage_gate`: PASS

## Sample diff (A vs B)
- 一致项：安装链、stage gate、预算/成本锚点、PM 可见性、outsider 预算/成本拒绝均一致 PASS。
- 差异项：
  - 新建记录 ID 不同（自然差异）：A `project_id=6/task_id=10/budget_id=3/cost_id=3`，B `project_id=2/task_id=3/budget_id=1/cost_id=1`
  - outsider 项目/任务可见性均为 `1`（两库一致观测）。

## Verification commands (key)
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-07-1292.yaml`
- PASS: `python3 scripts/verify/native_business_fact_install_order_guard_verify.py`
- PASS: 全部 sample A/B 安装与 verify 命令（按任务合同 acceptance 顺序执行）

## Risk analysis
- 风险等级：`high`（多 fresh 库连续验证）
- 本轮无 ACL/record-rule/manifest/前端改动。
- 当前可交付结论：新库“可重复成立”在两库抽样下成立；项目/任务 outsider 可见性仍是后续规则专题观测项。

## Rollback suggestion
- `git restore scripts/verify/native_business_fact_install_order_guard_verify.py`
- `git restore scripts/verify/native_business_fact_fresh_install_min_flow_verify.py`
- `git restore docs/ops/install_order_guard_min_rules_v1.md`

## Next iteration suggestion
- 继续 fresh-runtime 防再生 v1.1：再加一库抽样（第3库）并将“项目/任务 outsider 可见”转入独立权限专题，不在当前链路混入高风险 ACL 改动。
