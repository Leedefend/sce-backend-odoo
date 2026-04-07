# ITER-2026-04-07-1293 Report

## Summary
- 按用户要求执行“行业核心模块独立 fresh 验证”，且不提前宣告独立可靠。
- fresh 新库：`sc_prod_fresh_core_1293`
- 仅安装：`smart_construction_core`（及其依赖）
- 执行最小原生业务流（project/task/budget/cost/payment/settlement）并验证锚点与基础可见性。

## Verification
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-07-1293.yaml`
- PASS: `ENV=prod.sim ENV_FILE=.env.prod.sim make db.create DB=sc_prod_fresh_core_1293`
- PASS: `ENV=prod.sim ENV_FILE=.env.prod.sim make mod.install MODULE=smart_construction_core DB_NAME=sc_prod_fresh_core_1293`
- PASS: `DB_NAME=sc_prod_fresh_core_1293 E2E_BASE_URL=http://localhost:18079 ROLE_OWNER_LOGIN=admin ROLE_OWNER_PASSWORD=admin python3 scripts/verify/native_business_fact_core_standalone_min_flow_verify.py`

## Core standalone result (key observations)
- 新建业务对象均可创建：`project/task/budget/cost/payment/settlement`
- 锚点成立：`budget/cost/payment/settlement` 均与项目 `project/company` 对齐
- 可见性观测：outsider 对 `budget/cost/payment/settlement` 不可见；对 `project/task` 仍可见（`1`）

## Core vs current product-chain difference
- 对比库：`sc_prod_fresh_1292_b`（current product chain）
- 同一专用脚本复跑结论：
  - 两者一致：outsider 对 `budget/cost/payment/settlement` 不可见
  - 两者一致：outsider 对 `project/task` 可见（未隔离）
- 结论：当前证据不支持“core 独立可靠”宣告；project/task outsider 隔离缺口在 core-only 与 product-chain 中同样存在。

## Risk
- 评级：`PASS_WITH_RISK`
- 风险点：`project.project` / `project.task` outsider 默认可见，需进入独立权限专题修复。

## Next
- 启动独立专题：project/task outsider 权限规则治理（不混入 fresh-runtime 主线）。
