# Batch-Business-Fact-Button-Label-Correction

## 1. 本轮变更
- 目标：补齐业务事实页面按钮显示名中文化遗漏。
- 完成：
  - 修正项目表单统计按钮内部 `open_task_count` 的 `statinfo` 显示名，从 `Tasks` 改为 `任务`。
  - 保持按钮 action、权限和业务逻辑不变。
- 未完成：无。

## 2. 影响范围
- 模块：`smart_construction_core`
- 启动链：否
- contract：否
- 路由：否
- public intent：否

## 3. 风险
- P0：无。
- P1：无，仅视图显示名变更。
- P2：后续仍需关注按钮内部字段、statinfo、状态组件等非 `<button string>` 标签，避免普通按钮扫描漏检。

## 4. 验证
- 命令：
  - `python3 -m xml.etree.ElementTree addons/smart_construction_core/views/core/project_views.xml`
  - `git diff --check`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast CODEX_NEED_UPGRADE=1 COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make mod.upgrade MODULE=smart_construction_core`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make odoo.shell.exec`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make restart`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast E2E_LOGIN=wutao E2E_PASSWORD=123456 COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make verify.menu.navigation_snapshot.container`
- 结果：PASS。
- 标签事实：`action_view_tasks` 按钮 string 为 `任务`，内部 `open_task_count` statinfo string 为 `任务`。
- 导航快照：`PASS checked=139 scenes=16 trace=dc92cd99f7fb`。

## 5. 产物
- e2e：`/mnt/artifacts/codex/menu-navigation-field-snapshot/20260427T103749`
- trace：`dc92cd99f7fb`

## 6. 回滚
- 方法：回退本批 commit 后重新升级 `smart_construction_core`，并重启模拟生产后端。

## 7. 下一批次
- 目标：继续真实用户连续办理业务链路验证，遇到页面标签遗漏按事实审计补齐。
- 前置条件：继续使用模拟生产库 `sc_prod_sim`。
