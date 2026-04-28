# Batch-Business-Fact-Custom-Config-Page-Surface

## 1. 本轮变更
- 目标：继续清理真实用户可见页面中自定义业务配置页的英文标签、技术字段和导入痕迹。
- 完成：
  - 工程结构动作、菜单、视图与模型描述去除 `WBS` 页面字样，并补齐币种字段中文标签。
  - 物资计划 `state` 字段补中文标签。
  - 工程量清单移除来源表序号/来源表名称在表单上的展示。
  - 定额子目移除导入原始数据调试页和可见字段。
  - 阶段要求配置移除可见动作标识字段，模型字段标签改为业务化“办理入口”。
  - 定额导入向导将 `Excel/Sheet/header_row` 等可见文案改为中文业务表述。
- 未完成：`project.project` 与 `hr.department` 原生模型页面仍存在英文模型描述和英文字段标签。

## 2. 影响范围
- 模块：`smart_construction_core`, `sc_norm_engine`
- 启动链：否
- contract：否
- 路由：否
- public intent：否

## 3. 风险
- P0：无。
- P1：阶段要求配置不再在表单直接编辑动作标识，后续若需要开放给业务配置管理员，应提供“选择办理入口”的业务化控件，而不是暴露 XMLID。
- P2：剩余缺口集中在 Odoo 原生模型，下一批需要决定采用专用业务视图还是翻译/字段描述覆盖。

## 4. 验证
- 命令：
  - `python3 -m py_compile addons/sc_norm_engine/wizard/norm_import_wizard.py addons/smart_construction_core/wizard/quota_import_wizard.py addons/smart_construction_core/models/core/material_plan.py addons/smart_construction_core/models/core/project_core.py addons/smart_construction_core/models/core/boq.py addons/smart_construction_core/models/support/project_dictionary.py addons/smart_construction_core/models/support/project_stage_requirements.py`
  - `python3 -m xml.etree.ElementTree ...`
  - `git diff --check`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast CODEX_NEED_UPGRADE=1 COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make mod.upgrade MODULE=smart_construction_core`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast CODEX_NEED_UPGRADE=1 COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make mod.upgrade MODULE=sc_norm_engine`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make odoo.shell.exec < scripts/migration/business_fact_page_surface_audit_probe.py`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make restart`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast E2E_LOGIN=wutao E2E_PASSWORD=123456 COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make verify.menu.navigation_snapshot.container`
- 结果：PASS。
- 审计：`business_fact_page_surface_audit issue_count 52 -> 36`，剩余均为 `project.project` / `hr.department` 原生页面英文标签。
- 导航快照：`PASS checked=139 scenes=16 trace=a273cef735b5`。

## 5. 产物
- e2e：`/mnt/artifacts/codex/menu-navigation-field-snapshot/20260427T094658`
- trace：`a273cef735b5`

## 6. 回滚
- 方法：回退本批 commit 后重新升级 `smart_construction_core` 与 `sc_norm_engine`，并重启模拟生产环境。

## 7. 下一批次
- 目标：处理 `project.project` 项目原生页面与 `hr.department` 组织架构原生页面英文标签。
- 前置条件：优先评估是否用业务专用视图覆盖，避免直接改 Odoo 原生视图导致升级冲突。
