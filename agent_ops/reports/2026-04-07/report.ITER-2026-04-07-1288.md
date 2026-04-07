# ITER-2026-04-07-1288 Report

## Summary of execution
- 已按专项目标执行 fresh-runtime 验证链：
  1) 创建新库 `sc_prod_fresh_1288`
  2) 安装 `smart_construction_custom`（含依赖）
  3) 运行预算/成本严格锚点校验
  4) 运行 `verify.native.business_fact.stage_gate`

## Verification result
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-07-1288.yaml`
- PASS: fresh db 创建 + `mod.install smart_construction_custom`
- PASS: `DB_NAME=sc_prod_fresh_1288 E2E_BASE_URL=http://localhost:18079 ROLE_OWNER_LOGIN=wutao ROLE_OWNER_PASSWORD=demo BUDGET_COST_VERIFY_REQUIRE_PM_VISIBLE=false python3 scripts/verify/native_business_fact_budget_cost_member_visibility_verify.py`
  - 关键结果：`budget.project_without_company=0`、`cost.project_without_company=0`
- FAIL: `make verify.native.business_fact.stage_gate DB_NAME=sc_prod_fresh_1288 E2E_BASE_URL=http://localhost:18079`
  - 失败点：`scene_legacy_auth_smoke` 对 `/api/scenes/my` 返回 `404`（期望 401/403）

## Root-cause blocker
- fresh 库缺失场景链必要注册，导致 legacy scene auth endpoint 不可用。
- 尝试安装 `smart_construction_scene` 失败：
  - `Cannot update missing record 'smart_construction_core.sc_cap_group_project_management'`
  - 文件定位：`addons/smart_construction_scene/data/sc_scene_orchestration.xml:5`
- 数据对比证据：
  - `sc_prod_fresh_1288` 中 `ir_model_data` 不存在 `smart_construction_core.sc_cap_group_project_management`
  - `sc_prod_sim` 中该 external id 存在

## Risk analysis
- 本批次确认“锚点不再生”在 fresh 库成立（budget/cost 严格锚点 PASS）。
- 但“fresh stage gate 全通过”被 scene 链安装阻塞，属于真实交付阻断。

## Rollback suggestion
- 本批次未修改业务代码；如需回滚验证环境，删除数据库 `sc_prod_fresh_1288` 即可。

## Next iteration suggestion
- 启动专用修复线：`fresh-runtime scene install-order / external-id materialization`。
- 目标：修复 `smart_construction_scene` 对 `smart_construction_core.sc_cap_group_project_management` 的 fresh-install 可达性后，复跑 1288 stage gate。
