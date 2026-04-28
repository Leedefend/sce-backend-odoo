# Batch-Business-OCA-Reject-Material-Runtime

## 1. 本轮变更
- 目标：补齐付款/收款申请 OCA 驳回链路，并验证物资计划真实用户 OCA 审批通过/驳回连续办理。
- 完成：
  - `payment.request` 驳回回调优先读取 OCA `tier.review.comment` 作为审计原因；OCA 当前入口无评论时落明确默认原因，避免技术参数缺失阻断驳回。
  - `project.material.plan` 提交审批改为 `with_company(company)`，去除 Odoo 17 不再支持的 `force_company` 上下文 warning。
  - 用模拟生产库真实用户验证付款申请 OCA 驳回：`caisiqi/蔡思琪` 提交，`chenshuai/陈帅` 驳回，业务单据进入 `rejected`。
  - 用模拟生产库真实用户验证物资计划 OCA 审批：`zhaowei/赵伟` 提交，`chenshuai/陈帅` 审批；通过进入 `approved/validated`，驳回回到 `draft` 并保留驳回原因。
- 未完成：尚未把这两类回滚式探针固化为独立脚本入口；下一批可沉淀为 `scripts/verify`。

## 2. 影响范围
- 模块：`smart_construction_core`
- 启动链：否
- contract：否
- 路由：否

## 3. 风险
- P0：已处理。付款申请 OCA 驳回因缺少业务原因导致无法落业务状态。
- P1：已处理。物资计划提交保留旧 `force_company` 上下文，运行时产生 Odoo 17 warning。
- P2：付款申请在无 OCA 评论时使用默认驳回原因；后续若要求强制填写业务原因，应在 OCA 评论弹窗或前端动作层强约束。

## 4. 验证
- 命令：`python3 -m py_compile addons/smart_construction_core/models/core/payment_request.py addons/smart_construction_core/models/core/material_plan.py`
- 结果：PASS
- 命令：`git diff --check`
- 结果：PASS
- 命令：`ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast CODEX_NEED_UPGRADE=1 COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make mod.upgrade MODULE=smart_construction_core`
- 结果：PASS
- 命令：付款申请 OCA 驳回真实用户回滚式 Odoo shell 探针
- 结果：PASS，`PAYMENT_REQUEST_OCA_REJECT_SMOKE=PASS`，`BEFORE_REJECT submit waiting ['waiting']`，`AFTER_REJECT rejected rejected ['rejected']`
- 命令：物资计划 OCA 审批通过/驳回真实用户回滚式 Odoo shell 探针
- 结果：PASS，`MATERIAL_PLAN_OCA_APPROVE_REJECT_SMOKE=PASS`，`MATERIAL_AFTER_APPROVE approved validated ['approved']`，`MATERIAL_AFTER_REJECT draft no 0 未填写原因`
- 命令：`ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make restart`
- 结果：PASS
- 命令：`ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast E2E_LOGIN=caisiqi E2E_PASSWORD=123456 COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make verify.menu.navigation_snapshot.container`
- 结果：PASS，`checked=53 scenes=10 trace=cd254c6634d2`

## 5. 产物
- snapshot：`/mnt/artifacts/codex/menu-navigation-field-snapshot/20260427T121132`
- logs：Odoo shell 输出中的 `PAYMENT_REQUEST_OCA_REJECT_SMOKE=PASS`、`MATERIAL_PLAN_OCA_APPROVE_REJECT_SMOKE=PASS`
- e2e：N/A

## 6. 回滚
- commit：回退本批次提交。
- 方法：回退后执行 `make mod.upgrade MODULE=smart_construction_core` 并重启模拟生产服务。

## 7. 下一批次
- 目标：将付款申请、物资计划 OCA 真实用户办理探针沉淀为可重复执行脚本，并继续审计采购订单/结算单是否需要迁移到 OCA tier 执行层。
- 前置条件：继续使用模拟生产库真实用户，优先排除 demo/sc_fx/admin。
