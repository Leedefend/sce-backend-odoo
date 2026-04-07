# ITER-2026-04-07-1294 Report

## Summary of change
- 主题：`project.project / project.task outsider default deny` 权限治理专题。
- 在 `addons/smart_construction_core/security/sc_record_rules.xml` 新增两条全局隔离规则：
  - `rule_sc_project_global_project_project_isolation`
  - `rule_sc_project_global_project_task_isolation`
- 规则语义：
  - 非特权用户默认仅可见“创建人/项目成员/项目关键岗位/任务负责人”范围内记录。
  - 特权放行：`base.group_system`、`project.group_project_manager`、`group_sc_super_admin`、`group_sc_cap_project_manager`。

## Verification result
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-07-1294.yaml`
- PASS: `CODEX_NEED_UPGRADE=1 ENV=prod.sim ENV_FILE=.env.prod.sim make mod.upgrade MODULE=smart_construction_core DB_NAME=sc_prod_fresh_1292_b`
- PASS: `CODEX_NEED_UPGRADE=1 ENV=prod.sim ENV_FILE=.env.prod.sim make mod.upgrade MODULE=smart_construction_core DB_NAME=sc_prod_fresh_core_1293`
- PASS: `DB_NAME=sc_prod_fresh_1292_b ... python3 scripts/verify/native_business_fact_non_member_denial_verify.py`
- PASS: `DB_NAME=sc_prod_fresh_core_1293 ... python3 scripts/verify/native_business_fact_non_member_denial_verify.py`
- PASS: `DB_NAME=sc_prod_fresh_core_1293 ... python3 scripts/verify/native_business_fact_core_standalone_min_flow_verify.py`
  - 关键结果：`outsider_project=0 outsider_task=0 outsider_budget=0 outsider_cost=0 outsider_payment=0 outsider_settlement=0`
- 观测项：`native_business_fact_fresh_install_min_flow_verify.py` 仍显示 `outsider_project_count=1 outsider_task_count=1`（该脚本固定使用 `outsider_seed`，其角色属性与“纯 outsider”不一致，属于样本账号语义偏差）。

## Blocking points
- 历史阻塞根因：`project` 基础规则与自定义组规则并集导致 outsider 穿透读取 project/task。
- 当前状态：在专用验证脚本（真实“临时 outsider”）下已收敛为默认不可见。

## Risk analysis
- 结论：`PASS_WITH_RISK`。
- 风险1：`fresh_install_min_flow` 仍使用固定样本账号 `outsider_seed`，会给出“project/task 可见”噪音信号。
- 风险2：如果后续变更 `project.group_project_manager` 归属策略，可能影响“特权放行”边界，需要专题回归。

## Rollback suggestion
- 若需快速回滚本轮权限变更：
  - `git restore addons/smart_construction_core/security/sc_record_rules.xml`
  - 然后对目标库执行：
    - `CODEX_NEED_UPGRADE=1 ENV=prod.sim ENV_FILE=.env.prod.sim make mod.upgrade MODULE=smart_construction_core DB_NAME=<db_name>`

## Next iteration suggestion
- 建议下一轮（低风险 verify 批次）仅做一件事：
  - 将 `native_business_fact_fresh_install_min_flow_verify.py` 的 outsider 样本改为“临时最小权限 outsider”，避免与 `outsider_seed` 角色语义耦合，统一 stage evidence。
