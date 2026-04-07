# ITER-2026-04-07-1289 Report

## Summary of change
- 在 `addons/smart_construction_core/data/sc_capability_group_seed.xml` 恢复 fresh-runtime 必需的 core-owned XMLIDs：
  - capability groups（8个）
  - capabilities（5个）
  - default scene（1个）
- 目标是保证 `smart_construction_scene` 安装时对 `smart_construction_core.*` 的跨模块更新有可更新目标，消除 missing external id 阻断。

## Verification result
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-07-1289.yaml`
- PASS: `CODEX_NEED_UPGRADE=1 ENV=prod.sim ENV_FILE=.env.prod.sim make mod.upgrade MODULE=smart_construction_core DB_NAME=sc_prod_fresh_1288`
- PASS: `ENV=prod.sim ENV_FILE=.env.prod.sim make mod.install MODULE=smart_construction_scene DB_NAME=sc_prod_fresh_1288`
- PASS: `DB_NAME=sc_prod_fresh_1288 E2E_BASE_URL=http://localhost:18079 ROLE_OWNER_LOGIN=wutao ROLE_OWNER_PASSWORD=demo BUDGET_COST_VERIFY_REQUIRE_PM_VISIBLE=false python3 scripts/verify/native_business_fact_budget_cost_member_visibility_verify.py`
- PASS: `ROLE_OWNER_LOGIN=wutao ROLE_OWNER_PASSWORD=demo ROLE_PM_LOGIN=xiaohuijiu ROLE_PM_PASSWORD=demo ROLE_FINANCE_LOGIN=shuiwujingbanren ROLE_FINANCE_PASSWORD=demo ROLE_EXECUTIVE_LOGIN=wennan ROLE_EXECUTIVE_PASSWORD=demo E2E_BASE_URL=http://localhost:18079 make verify.native.business_fact.stage_gate DB_NAME=sc_prod_fresh_1288`

## Runtime note
- 为确保 `scene_legacy_auth_smoke` 在未登录态返回真实 401/403，本轮临时验证实例采用单库过滤：`ODOO_DBFILTER=^sc_prod_fresh_1288$`（端口 `18079`）。
- 验证结束后已清理临时容器并恢复默认 `ENV=prod.sim` 服务编排。

## Risk analysis
- 风险等级：`high`（fresh-runtime 安装链恢复批次）。
- 实际影响面受控：仅改动 capability/scene seed 数据，不涉及 ACL、record rule、manifest、财务语义。
- 验证显示目标阻断已解除，fresh stage gate 恢复通过。

## Rollback suggestion
- `git restore addons/smart_construction_core/data/sc_capability_group_seed.xml`
- 重新执行 core 升级：`CODEX_NEED_UPGRADE=1 ENV=prod.sim ENV_FILE=.env.prod.sim make mod.upgrade MODULE=smart_construction_core DB_NAME=sc_prod_fresh_1288`

## Next suggestion
- 启动下一轮 fresh-runtime 防再生专项，聚焦“新库安装顺序稳定性 + 锚点不回退”长期守卫。
