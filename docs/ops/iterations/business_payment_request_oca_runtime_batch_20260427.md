# Batch-Business-Payment-Request-OCA-Runtime

## 1. 本轮变更
- 目标：验证并补齐付款/收款申请从真实用户提交到 OCA 审批通过的连续办理链路。
- 完成：
  - 修复 `payment.request` OCA server action 回调在 OCA 仅传入 `active_model/active_id` 时取不到 `records` 的问题。
  - 同步修复 `project.material.plan` OCA 回调目标记录解析，避免同类审批回调断链。
  - 将付款申请资金基线读取与项目已占用金额统计改为服务端受控读取，普通内部发起人无需直接拥有资金基线模型权限。
  - 将付款申请、物资计划的 chatter 提示改为非阻断写入，真实用户未配置发件邮箱不再阻断业务提交/审批。
  - 增加付款申请权限回归用例，覆盖业务发起人无资金基线 ACL 时仍可提交的路径。
- 未完成：驳回链路尚未用真实用户做独立回滚式探针；下一批继续补。

## 2. 影响范围
- 模块：`smart_construction_core`
- 启动链：否
- contract：否
- 路由：否

## 3. 风险
- P0：已处理。OCA 审批通过后业务单据不落 `approved`，真实启用会形成已审未推进单据。
- P1：已处理。真实发起人没有资金基线 ACL 或邮箱时，付款申请提交被系统技术配置阻断。
- P2：chatter 失败现在只记录 warning，不再强制失败；后续若需要通知可靠性，应单独治理邮件配置。

## 4. 验证
- 命令：`python3 -m py_compile addons/smart_construction_core/models/core/payment_request.py addons/smart_construction_core/models/core/material_plan.py addons/smart_construction_core/tests/test_payment_request_permission.py`
- 结果：PASS
- 命令：`git diff --check`
- 结果：PASS
- 命令：`ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast CODEX_NEED_UPGRADE=1 COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make mod.upgrade MODULE=smart_construction_core`
- 结果：PASS
- 命令：真实用户回滚式 Odoo shell 探针
- 结果：PASS，`REAL_ACTORS caisiqi 蔡思琪 | chenshuai 陈帅`，`REAL_AFTER_SUBMIT submit waiting 1 ['waiting']`，`REAL_AFTER_VALIDATE approved validated ['approved']`，`REAL_PAYMENT_REQUEST_OCA_TIER_SMOKE=PASS`
- 命令：`ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make restart`
- 结果：PASS
- 命令：`ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast E2E_LOGIN=caisiqi E2E_PASSWORD=123456 COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make verify.menu.navigation_snapshot.container`
- 结果：PASS，`checked=53 scenes=10 trace=aa27292c384f`

## 5. 产物
- snapshot：`/mnt/artifacts/codex/menu-navigation-field-snapshot/20260427T115830`
- logs：Odoo shell 输出中的 `REAL_PAYMENT_REQUEST_OCA_TIER_SMOKE=PASS`
- e2e：N/A

## 6. 回滚
- commit：回退本批次提交。
- 方法：回退后执行 `make mod.upgrade MODULE=smart_construction_core` 并重启模拟生产服务。

## 7. 下一批次
- 目标：补齐付款/收款申请 OCA 驳回链路真实用户验证，并继续扩展到物资计划审批通过/驳回真实办理探针。
- 前置条件：继续使用模拟生产库真实用户，优先排除 demo/sc_fx/admin。
