# Batch-Business-OCA-Runtime-Smoke-Guard

## 1. 本轮变更
- 目标：把付款申请、物资计划 OCA 真实用户办理探针沉淀为可重复执行入口。
- 完成：
  - 新增 `scripts/verify/business_oca_runtime_smoke.py`，在 Odoo shell 中创建临时业务数据，覆盖付款申请审批通过/驳回、物资计划审批通过/驳回四条链路。
  - 新增 `make verify.business.oca_runtime_smoke`，复用项目现有 `scripts/ops/odoo_shell_exec.sh` 执行脚本。
  - 脚本默认排除 `admin`、`demo*`、`sc_fx*`，优先使用真实用户 `caisiqi -> chenshuai` 和 `zhaowei -> chenshuai`，也支持通过环境变量覆盖。
  - 脚本在 finally 中统一 rollback，只做可用性验证，不污染模拟生产库。
- 未完成：采购订单/结算单是否迁移到 OCA tier 执行层尚未审计。

## 2. 影响范围
- 模块：`scripts/verify`、`Makefile`
- 启动链：否
- contract：否
- 路由：否

## 3. 风险
- P0：无业务数据写入风险，脚本最终 rollback。
- P1：脚本依赖真实用户仍存在且拥有对应能力组；若用户配置变化，可用环境变量覆盖提交人/审批人。
- P2：脚本只覆盖当前已接入 OCA tier 的付款申请与物资计划，不代表全部审批业务已经 OCA 化。

## 4. 验证
- 命令：`python3 -m py_compile scripts/verify/business_oca_runtime_smoke.py`
- 结果：PASS
- 命令：`git diff --check`
- 结果：PASS
- 命令：`ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make verify.business.oca_runtime_smoke`
- 结果：PASS，`BUSINESS_OCA_RUNTIME_SMOKE=PASS`，`BUSINESS_OCA_RUNTIME_ROLLBACK=OK`

## 5. 产物
- snapshot：N/A
- logs：`make verify.business.oca_runtime_smoke` 输出中的四条链路标记。
- e2e：N/A

## 6. 回滚
- commit：回退本批次提交。
- 方法：移除 Makefile 目标和 `scripts/verify/business_oca_runtime_smoke.py`。

## 7. 下一批次
- 目标：审计采购订单、结算单、费用/保证金等 document_state 审批业务是否需要迁移到 OCA tier 执行层，明确“业务配置规则”和“OCA执行层”的边界。
- 前置条件：继续使用模拟生产库真实用户和本批新增 smoke 作为 OCA 基线。
