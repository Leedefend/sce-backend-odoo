# Batch-Business-Fact-Native-Project-Org-Page-Surface

## 1. 本轮变更
- 目标：清理真实用户可见的 `project.project` 项目页面与 `hr.department` 组织架构页面英文标签。
- 完成：
  - `project.project` 模型描述改为“项目”，并补齐项目原生字段中文业务标签。
  - 项目概览、项目管理、项目清单动作绑定已存在的业务化项目视图与搜索视图，避免落回 Odoo 原生英文视图。
  - `hr.department` 模型描述改为“组织架构”，补齐部门原生字段中文业务标签。
  - 组织架构新增业务专用 tree/form/search 视图，并绑定到业务配置菜单动作。
  - 项目状态与更新时间等残留英文字段标签完成中文化。
- 未完成：无。本轮审计范围内业务事实页面英文标签缺口已清零。

## 2. 影响范围
- 模块：`smart_construction_core`
- 启动链：否
- contract：否
- 路由：否
- public intent：否

## 3. 风险
- P0：无。
- P1：项目与组织架构覆盖了 Odoo 原生模型字段标签，后续若引入其他依赖模块新增默认视图，仍需通过业务动作显式绑定业务视图。
- P2：组织架构仍以部门承载分公司/部门类组织信息；平台级独立公司创建能力未开放给业务用户，符合当前收口要求。

## 4. 验证
- 命令：
  - `python3 -m py_compile addons/smart_construction_core/models/core/project_core.py addons/smart_construction_core/models/support/organization_department.py addons/smart_construction_core/models/support/__init__.py`
  - `python3 -m xml.etree.ElementTree addons/smart_construction_core/views/support/organization_department_views.xml`
  - `python3 -m xml.etree.ElementTree addons/smart_construction_core/actions/project_list_actions.xml`
  - `python3 -m xml.etree.ElementTree addons/smart_construction_core/views/projection/project_dashboard_kanban.xml`
  - `python3 -m xml.etree.ElementTree addons/smart_construction_core/actions/project_actions.xml`
  - `python3 -m xml.etree.ElementTree addons/smart_construction_core/actions/project_native_action_overrides.xml`
  - `python3 -m xml.etree.ElementTree addons/smart_construction_core/views/core/project_views.xml`
  - `python3 -m xml.etree.ElementTree addons/smart_construction_core/views/core/project_list_views.xml`
  - `git diff --check`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast CODEX_NEED_UPGRADE=1 COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make mod.upgrade MODULE=smart_construction_core`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make odoo.shell.exec < scripts/migration/business_fact_page_surface_audit_probe.py`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make restart`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast E2E_LOGIN=wutao E2E_PASSWORD=123456 COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make verify.menu.navigation_snapshot.container`
- 结果：PASS。
- 审计：`business_fact_page_surface_audit issue_count 36 -> 0`，`decision=business_page_surface_ready`。
- 导航快照：`PASS checked=139 scenes=16 trace=4d257fd37a66`。

## 5. 产物
- e2e：`/mnt/artifacts/codex/menu-navigation-field-snapshot/20260427T095915`
- trace：`4d257fd37a66`

## 6. 回滚
- 方法：回退本批 commit 后重新升级 `smart_construction_core`，并重启模拟生产环境。

## 7. 下一批次
- 目标：从页面表面清理转入真实用户连续办理业务链路验证，输出真实可用用户矩阵与业务数据缺口。
- 前置条件：继续使用模拟生产库 `sc_prod_sim` 与真实用户 `wutao` 等初始化账号进行验证。
