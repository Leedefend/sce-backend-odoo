# 项目组织落位与隔离验收 v1

## 验收范围
- 运行可达（严格模式）
- 真实角色链路
- 关键对象隔离锚点
- 关键流程可办

## 验收命令
- `ROLE_OWNER_LOGIN=wutao ROLE_OWNER_PASSWORD=demo ROLE_PM_LOGIN=xiaohuijiu ROLE_PM_PASSWORD=demo ROLE_FINANCE_LOGIN=shuiwujingbanren ROLE_FINANCE_PASSWORD=demo ROLE_EXECUTIVE_LOGIN=wennan ROLE_EXECUTIVE_PASSWORD=demo E2E_BASE_URL=http://localhost:18069 make verify.native.business_fact.stage_gate DB_NAME=sc_prod_sim`

## 正式验证脚本清单（outsider 默认拒绝）
- `scripts/verify/native_business_fact_fresh_install_min_flow_verify.py`
- `scripts/verify/native_business_fact_non_member_denial_verify.py`
- `scripts/verify/native_business_fact_core_standalone_min_flow_verify.py`
- `scripts/verify/native_business_fact_native_operability_closure_verify.py`
- `scripts/verify/native_business_fact_payment_settlement_operability_verify.py`

说明：
- `native_business_fact_fresh_install_min_flow_verify.py` 已统一 outsider 语义：默认不再依赖 `outsider_seed`，改为运行期创建临时最小权限 outsider（仅 `base.group_user`），验证后自动清理。
- outsider 验证口径：`project/task/budget/cost` 对非成员默认不可见（`count=0` 或无读取权限）。

## 通过标准
- `scene_legacy_auth_smoke` 严格模式通过（运行可达不再伪 PASS）。
- `native_business_fact_isolation_anchor_verify` 通过（关键对象隔离锚点齐备）。
- `native_business_fact_role_operability_blockers_smoke` 通过（关键对象可办）。
- `product_project_flow_full_chain_execution_smoke` 通过（真实角色链路）。

## 冻结结论（v1）
- `project.project` / `project.task` / `project.budget` / `project.cost.ledger` / `payment.request` / `sc.settlement.order` 已进入“非成员默认拒绝”验证结论。
- 特权放行边界：`base.group_system`、`project.group_project_manager`、`smart_construction_core.group_sc_super_admin`、`smart_construction_core.group_sc_cap_project_manager`。
- 在 fresh 库与 core-only fresh 库上，`fresh_install_min_flow` 与 `non_member_denial` 证据口径一致，项目级默认拒绝结论由 `PASS_WITH_RISK` 收敛为 `PASS`。

## 原生最小办理闭环（v1）
- 验证库：`sc_prod_fresh_1292_b`
- 验证脚本：`native_business_fact_native_operability_closure_verify.py`
- 闭环证据：
  - 项目：owner 可创建项目并维护关键岗位字段，成员载体可维护并保存成功。
  - 任务：PM 可创建任务、编辑任务并执行关键状态推进（stage 写入）。
  - 预算/成本：PM 作为授权成员可创建预算与成本，且 `project_id/company_id` 锚点自动继承成立。
- outsider：对 project/task/budget/cost 默认不可见且不可写。

## 支付/结算最小办理闭环（v1）
- 验证库：`sc_prod_fresh_1292_b`
- 验证脚本：`native_business_fact_payment_settlement_operability_verify.py`
- 闭环证据：
  - finance 授权成员可创建并编辑 `payment.request`。
  - finance 授权成员可创建并编辑 `sc.settlement.order`。
  - `payment.request` 与 `sc.settlement.order` 的 `project_id/company_id` 锚点自动继承成立。
  - outsider 对 `payment.request` / `sc.settlement.order` 默认不可见且不可写。

## 非本轮范围（需高风险闸门）
- `ACL` 文件直接改写。
- `record_rules/**` 直接改写。
