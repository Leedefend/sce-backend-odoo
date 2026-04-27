# Batch-Business-Document-State-Policy-Switch

## 1. 本轮变更
- 目标：验证并固化“用户配置需要审批就走审批，取消审批就不走审批”的 document_state 运行语义。
- 完成：
  - 新增 `scripts/verify/business_document_state_policy_switch_smoke.py`。
  - 新增 `make verify.business.document_state_policy_switch`。
  - 覆盖费用/保证金、结算单、采购订单三类代表业务：
    - 费用/保证金：开启审批时提交到 `submit`；关闭审批时提交直达 `approved`。
    - 结算单：开启审批时提交到 `submit`；关闭审批时提交直达 `approve`。
    - 采购订单：开启审批时非采购审批人确认被拦截；关闭审批时非审批人可确认到 `purchase`。
  - 脚本使用事务回滚，不污染模拟生产库。
- 未完成：项目合同、一般合同、采购/一般合同还需要同样沉淀到开关 smoke；是否迁移到 OCA tier 执行层另起批次审计。

## 2. 影响范围
- 模块：`scripts/verify`、`Makefile`
- 启动链：否
- contract：否
- 路由：否

## 3. 风险
- P0：无业务数据写入风险，脚本最终 rollback。
- P1：采购订单验证创建临时采购用户，仅事务内存在；若未来权限模型变更，需要同步更新脚本。
- P2：本批验证 document_state 运行语义，不代表已全部迁移到 OCA tier。

## 4. 验证
- 命令：`python3 -m py_compile scripts/verify/business_document_state_policy_switch_smoke.py`
- 结果：PASS
- 命令：`git diff --check`
- 结果：PASS
- 命令：`ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make verify.business.document_state_policy_switch`
- 结果：PASS，`BUSINESS_DOCUMENT_STATE_POLICY_SWITCH_SMOKE=PASS`，`BUSINESS_DOCUMENT_STATE_POLICY_SWITCH_ROLLBACK=OK`

## 5. 产物
- snapshot：N/A
- logs：`make verify.business.document_state_policy_switch` 输出。
- e2e：N/A

## 6. 回滚
- commit：回退本批次提交。
- 方法：移除 Makefile 目标和 `scripts/verify/business_document_state_policy_switch_smoke.py`。

## 7. 下一批次
- 目标：补齐合同类 document_state 开关 smoke，并审计哪些 document_state 业务需要进一步迁移到 OCA tier 执行层。
- 前置条件：继续使用模拟生产库真实配置，保持审批规则作为业务真源。
