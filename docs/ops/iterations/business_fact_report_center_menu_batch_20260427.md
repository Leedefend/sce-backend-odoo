# Batch-Business-Fact-Report-Center-Menu

## 1. 本轮变更
- 目标：将真实用户可见的“数据分析”调整为报表/台账语义，避免数据字典占据分析入口。
- 完成：
  - 顶层 `menu_sc_data_center` 从“数据分析”改名为“报表中心”。
  - 报表中心父菜单能力组扩展为数据、成控、财务相关能力组，保证台账迁移后对应用户仍可见。
  - 成本台账、成本报表、经营利润迁入报表中心。
  - 支付台账、资金台账、收款台账、融资台账、资金日报、资金日报明细迁入报表中心。
  - 旧“业务字典”入口不再挂在报表中心，并收口到 `base.group_no_one`；业务配置下保留规范化的数据字典分类入口。
  - 前端兜底导航标签从“数据分析”同步为“报表中心”。
- 未完成：无。本轮只处理菜单语义和归属，不调整单据办理入口。

## 2. 影响范围
- 模块：`smart_construction_core`
- 启动链：否
- contract：否
- 路由：否
- public intent：否

## 3. 风险
- P0：无。
- P1：部分用户习惯从成本管理或财务账款进入台账；本轮将台账集中到报表中心，但 action/xmlid 不变，场景和快捷入口仍可继续定位。
- P2：报表中心目前承载台账和报表，后续若引入 BI 汇总页，应继续挂在该中心，避免回流到业务配置。

## 4. 验证
- 命令：
  - `python3 -m xml.etree.ElementTree addons/smart_construction_core/views/menu.xml`
  - `python3 -m xml.etree.ElementTree addons/smart_construction_core/views/support/dictionary_views.xml`
  - `python3 -m xml.etree.ElementTree addons/smart_construction_core/security/action_groups_patch.xml`
  - `git diff --check`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast CODEX_NEED_UPGRADE=1 COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make mod.upgrade MODULE=smart_construction_core`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make odoo.shell.exec`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make restart`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast FRONTEND_PROFILE=prod-sim COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make frontend.restart`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast E2E_LOGIN=wutao E2E_PASSWORD=123456 COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make verify.menu.navigation_snapshot.container`
- 结果：PASS。
- 菜单事实：`menu_sc_data_center=报表中心`；成本/财务台账与报表父级均为“报表中心”；旧 `menu_sc_dictionary` 仅 `Technical Features` 可见。
- 导航快照：`PASS checked=137 scenes=14 trace=25962173cc4e`。

## 5. 产物
- e2e：`/mnt/artifacts/codex/menu-navigation-field-snapshot/20260427T102547`
- trace：`25962173cc4e`

## 6. 回滚
- 方法：回退本批 commit 后重新升级 `smart_construction_core`，并重启模拟生产前后端。

## 7. 下一批次
- 目标：继续基于真实用户菜单验证可连续办理业务链路，判断是否存在办理入口或角色能力组缺口。
- 前置条件：继续使用模拟生产库 `sc_prod_sim` 与真实业务用户登录验证。
