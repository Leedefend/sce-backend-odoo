# Batch-Business-Fact-Cost-Misc-Page-Surface

## 1. 本轮变更
- 目标：继续清理真实用户可见业务页面中的英文标签、技术来源字段和非业务展示项。
- 完成：
  - 成本台账移除 `source_model/source_id/source_line_id` 可见来源块。
  - 成本台账、成本预算与实际、项目经营利润、进度计量、工程资料、工程结构相关字段去除 `WBS` 和 `YYYY-MM` 页面噪音。
  - 资金、结算、费用、收款、融资、合同对账等剩余英文模型描述和 `Active/Currency/Contract Amount` 等字段标签中文化。
- 未完成：`project.project`、`hr.department` 原生页面，以及定额/阶段配置少量技术字段仍在审计结果中。

## 2. 影响范围
- 模块：`addons/smart_construction_core`
- 启动链：否
- contract：否
- 路由：否
- public intent：否

## 3. 风险
- P0：无。
- P1：`project.cost.ledger.period` 与 `period_id` 标签同为“期间”，Odoo 升级时提示重复标签；不影响运行，但下一批可判断是否保留两个字段同时展示。
- P2：原生 `project.project` / `hr.department` 标签需要单独以业务视图或翻译覆盖处理，不能混入本批。

## 4. 验证
- 命令：
  - `python3 -m py_compile ...`
  - `python3 -m xml.etree.ElementTree addons/smart_construction_core/views/core/cost_domain_views.xml`
  - `git diff --check`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast CODEX_NEED_UPGRADE=1 COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make mod.upgrade MODULE=smart_construction_core`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make odoo.shell.exec < scripts/migration/business_fact_page_surface_audit_probe.py`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make restart`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast E2E_LOGIN=wutao E2E_PASSWORD=123456 COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make verify.menu.navigation_snapshot.container`
- 结果：PASS。
- 审计：`business_fact_page_surface_audit issue_count 85 -> 52`。
- 导航快照：`PASS checked=139 scenes=16 trace=31bd218c4955`。

## 5. 产物
- e2e：`/mnt/artifacts/codex/menu-navigation-field-snapshot/20260427T093732`
- trace：`31bd218c4955`

## 6. 回滚
- 方法：回退本批 commit 后重新执行 `make mod.upgrade MODULE=smart_construction_core` 并重启模拟生产环境。

## 7. 下一批次
- 目标：处理剩余 52 项中的项目/组织架构原生页面英文标签，以及定额子目、阶段要求配置中的技术字段。
- 前置条件：需先判断 `project.project` 与 `hr.department` 是采用专用业务视图覆盖，还是通过翻译/字段描述补齐。
