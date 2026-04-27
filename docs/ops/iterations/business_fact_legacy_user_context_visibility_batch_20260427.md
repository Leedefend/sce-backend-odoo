# Batch-Business-Fact-Legacy-User-Context-Visibility

## 1. 本轮变更
- 目标：判断并收口真实业务用户可见面中的 `历史用户权限` 页面。
- 完成：
  - 确认 `历史用户权限`、`历史用户`、`历史角色投影`、`项目授权范围` 属于迁移权限投影和项目授权追溯面，不是业务办理页面。
  - 将 3 个 action 和 4 个 menu 从 `group_sc_cap_data_read` 收口到 `group_sc_cap_config_admin`。
  - 对 4 个 `ir.ui.menu.groups_id` 增加显式替换记录，避免 Odoo 升级后旧数据分析组残留。
- 未完成：全量审计仍有 85 项缺口，集中在 Odoo 原生项目/组织架构视图、成本台账、物资计划、少量财务模型描述和 active 字段标签。

## 2. 影响范围
- 模块：`addons/smart_construction_core`
- 文件：
  - `views/support/legacy_user_context_views.xml`
- 启动链：否
- contract/schema：否
- default_route：否
- public intent：否

## 3. 风险
- P0：无已知 P0。本批次不删除数据、不调整真实用户和权限投影数据，只改变菜单/action 可见性。
- P1：数据分析只读用户不再能通过菜单访问历史权限追溯页面；该页面改由平台配置管理员进行迁移核查。
- P2：模型访问规则仍保留内部用户读权限，后续如需要彻底收口可单独评估 ACL，但本批次只收口真实用户菜单面。

## 4. 验证
- 命令：
  - `XML_PARSE_OK for addons/smart_construction_core/views/support/legacy_user_context_views.xml`
  - `rg group_sc_cap_data_read/group_sc_internal_user in legacy_user_context_views.xml`
  - `git diff --check`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast CODEX_NEED_UPGRADE=1 COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make mod.upgrade MODULE=smart_construction_core`
  - `LEGACY_USER_CONTEXT_FACTS` probe for `wutao`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make odoo.shell.exec < scripts/migration/business_fact_page_surface_audit_probe.py`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make restart`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" E2E_LOGIN=wutao E2E_PASSWORD=123456 make verify.menu.navigation_snapshot.container`
- 结果：
  - `LEGACY_USER_CONTEXT_FACTS.visible_for_wutao=[]`
  - 4 个历史用户权限菜单组均为 `smart_construction_core.group_sc_cap_config_admin`
  - `business_fact_page_surface_audit` issue_count `136 -> 85`
  - 导航快照：PASS，trace=`42ecdeb09325`

## 5. 产物
- menu snapshot artifact：`/mnt/artifacts/codex/menu-navigation-field-snapshot/20260427T093055`
- 页面审计脚本：`scripts/migration/business_fact_page_surface_audit_probe.py`
- 数据库：`sc_prod_sim`

## 6. 回滚
- commit：回退本批次提交。
- 方法：恢复 `legacy_user_context_views.xml` 中 action/menu groups 后执行 `make mod.upgrade MODULE=smart_construction_core`，再执行 `make restart`。

## 7. 下一批次
- 目标：处理剩余真实业务页面缺口，优先组织架构原生视图和项目原生视图英文标签；成本台账中 `source_model/source_id` 仍需单独收口。
- 前置条件：保持 `wutao` 作为真实业务用户验证样本；内部迁移追溯页继续只允许平台配置管理员访问。
