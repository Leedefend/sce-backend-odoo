# Batch-Business-Fact-Dictionary-Menu-Correction

## 1. 本轮变更
- 目标：纠正上一轮将“业务字典”隐藏导致业务配置管理员可能失去全局业务字典维护入口的问题。
- 完成：
  - 明确两类字典事实：
    - `sc.dictionary`：全局业务字典，支撑项目类型、项目类别、资料分类、合同类别等业务配置。
    - `project.dictionary`：定额/工程项目字典，支撑专业、章节、定额项目、子目及定额导入。
  - 恢复业务配置下 `业务字典` 菜单，指向 `action_sc_dictionary_manage` / `sc.dictionary`。
  - 将原业务配置下 `数据字典` 改名为 `定额字典`，避免与全局业务字典混淆。
  - 将 `全部字典` 改为 `全部定额字典`，action 标题改为 `定额字典（全部）`。
- 未完成：无。本轮只修正菜单语义和入口归属，不调整字典模型结构。

## 2. 影响范围
- 模块：`smart_construction_core`
- 启动链：否
- contract：否
- 路由：否
- public intent：否

## 3. 风险
- P0：无。
- P1：`project.dictionary` 仍保留少量历史类型（如 `project_type/cost_item/uom`）以兼容旧数据；菜单已按当前主要用途命名为定额字典，后续可再做数据迁移或类型拆分。
- P2：`core_extension.py` 仍有旧 `menu_sc_dictionary` / `action_project_dictionary` 映射名，当前未影响菜单可用性，后续若做场景语义映射清理应一并调整。

## 4. 验证
- 命令：
  - `python3 -m xml.etree.ElementTree addons/smart_construction_core/views/support/dictionary_views.xml`
  - `python3 -m xml.etree.ElementTree addons/smart_construction_core/security/action_groups_patch.xml`
  - `git diff --check`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast CODEX_NEED_UPGRADE=1 COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make mod.upgrade MODULE=smart_construction_core`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make odoo.shell.exec`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make restart`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast E2E_LOGIN=wutao E2E_PASSWORD=123456 COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make verify.menu.navigation_snapshot.container`
- 结果：PASS。
- 菜单事实：`业务配置 / 业务字典 -> sc.dictionary`；`业务配置 / 定额字典 / 全部定额字典 -> project.dictionary`。
- 导航快照：`PASS checked=139 scenes=16 trace=090e9d4984b1`。

## 5. 产物
- e2e：`/mnt/artifacts/codex/menu-navigation-field-snapshot/20260427T103120`
- trace：`090e9d4984b1`

## 6. 回滚
- 方法：回退本批 commit 后重新升级 `smart_construction_core`，并重启模拟生产后端。

## 7. 下一批次
- 目标：继续真实用户连续办理业务链路验证，重点检查业务配置管理员是否具备必要基础配置能力。
- 前置条件：继续使用模拟生产库 `sc_prod_sim` 与真实用户验证菜单和业务办理入口。
