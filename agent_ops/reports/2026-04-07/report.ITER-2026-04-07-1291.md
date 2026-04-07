# ITER-2026-04-07-1291 Report

## Summary of change
- 对 `addons/smart_construction_core/data/sc_capability_group_seed.xml` 做 install-order 安全修复：
  - 移除 4 个 capability seed 中提前依赖安全组 XMLID 的 `required_group_ids` 字段。
- 保留 capability group/capability/default scene 的核心 external-id 物化，确保 scene 模块仍可更新这些记录。

## Verification result
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-07-1291.yaml`
- PASS: `ENV=prod.sim ENV_FILE=.env.prod.sim make db.create DB=sc_prod_fresh_1291`
- PASS: `ENV=prod.sim ENV_FILE=.env.prod.sim make mod.install MODULE=smart_construction_custom DB_NAME=sc_prod_fresh_1291`
- PASS: `ENV=prod.sim ENV_FILE=.env.prod.sim make mod.install MODULE=smart_construction_scene DB_NAME=sc_prod_fresh_1291`
- PASS: `DB_NAME=sc_prod_fresh_1291 E2E_BASE_URL=http://localhost:18079 ROLE_OWNER_LOGIN=wutao ROLE_OWNER_PASSWORD=demo BUDGET_COST_VERIFY_REQUIRE_PM_VISIBLE=false python3 scripts/verify/native_business_fact_budget_cost_member_visibility_verify.py`
- PASS: `ROLE_OWNER_LOGIN=wutao ROLE_OWNER_PASSWORD=demo ROLE_PM_LOGIN=xiaohuijiu ROLE_PM_PASSWORD=demo ROLE_FINANCE_LOGIN=shuiwujingbanren ROLE_FINANCE_PASSWORD=demo ROLE_EXECUTIVE_LOGIN=wennan ROLE_EXECUTIVE_PASSWORD=demo E2E_BASE_URL=http://localhost:18079 make verify.native.business_fact.stage_gate DB_NAME=sc_prod_fresh_1291`

## Runtime note
- 临时验证实例使用单库过滤：`ODOO_DBFILTER=^sc_prod_fresh_1291$`（端口 `18079`），确保未登录 `/api/scenes/my` 路由落到目标库并返回 401。
- 验证完成后已清理临时容器并恢复默认 `prod.sim` 服务编排。

## Risk analysis
- 风险等级：`high`（fresh 安装链恢复）
- 风险收敛：改动仅限 seed 中早期依赖字段，不触碰 ACL、record rule、manifest、财务语义。

## Rollback suggestion
- `git restore addons/smart_construction_core/data/sc_capability_group_seed.xml`
- 然后重跑 fresh 安装验证确认回滚状态。

## Next iteration suggestion
- 可启动下一轮“fresh-runtime 连续防再生”专项，聚焦：
  - 新库重复验证稳定性（抽样多库）
  - install-order 回归守卫常态化
