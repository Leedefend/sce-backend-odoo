# Batch-Business-Fact-Core-Execution-Page-Surface

## 1. 本轮变更
- 目标：继续清理真实业务用户可见的核心办理页面，优先收口施工日志、付款执行、发票登记、综合合同中暴露的迁移字段、历史来源分组和英文模型描述。
- 完成：
  - `施工日志`、`付款执行`、`发票登记`、`综合合同` 模型 `_description` 中文化。
  - 上述页面移除 `source_origin`、`legacy_*` 字段展示，以及“历史迁移/新系统登记/历史来源”搜索和分组入口。
  - 页面只保留业务办理字段、状态、业务类型、项目/合同/往来单位、金额、日期、备注等用户可理解字段。
  - `综合合同` 新增只读业务别名 `install_commissioning_payment`，避免页面直接展示字段名包含 `debug` 的底层字段。
  - 相关 `active` 字段补中文标签，减少英文默认标签。
- 未完成：全量审计仍有 136 项缺口，集中在历史用户权限、组织架构原生视图、项目原生视图、成本台账、工程资料、物资计划及少量财务模型描述/active 标签。

## 2. 影响范围
- 模块：`addons/smart_construction_core`
- 文件：
  - `models/core/construction_diary.py`
  - `models/core/payment_execution.py`
  - `models/core/invoice_registration.py`
  - `models/core/general_contract.py`
  - `views/core/construction_diary_views.xml`
  - `views/core/payment_execution_views.xml`
  - `views/core/invoice_registration_views.xml`
  - `views/core/general_contract_views.xml`
- 启动链：否
- contract/schema：否
- default_route：否
- public intent：否

## 3. 风险
- P0：无已知 P0。本批次不删除字段、不迁移数据，只调整业务用户页面可见面。
- P1：历史迁移单据仍通过 `state == legacy_confirmed` 控制只读，页面不再展示来源字段；管理员追溯仍依赖底层字段和内部工具。
- P2：`install_commissioning_payment` 是非存储只读别名，仅用于页面展示；若后续需要排序/导出，应再评估存储化。

## 4. 验证
- 命令：
  - `python3 -m py_compile addons/smart_construction_core/models/core/construction_diary.py addons/smart_construction_core/models/core/payment_execution.py addons/smart_construction_core/models/core/invoice_registration.py addons/smart_construction_core/models/core/general_contract.py`
  - `XML_PARSE_OK for 4 changed XML files`
  - `rg visible legacy/source/debug fields in changed views`
  - `git diff --check`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast CODEX_NEED_UPGRADE=1 COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make mod.upgrade MODULE=smart_construction_core`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make odoo.shell.exec < scripts/migration/business_fact_page_surface_audit_probe.py`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make restart`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" E2E_LOGIN=wutao E2E_PASSWORD=123456 make verify.menu.navigation_snapshot.container`
- 结果：
  - `business_fact_page_surface_audit` issue_count `233 -> 136`
  - `施工日志`、`付款执行`、`发票登记`、`综合合同` 不再出现在高集中缺口列表。
  - 导航快照：PASS，trace=`1d9f8e8752f6`

## 5. 产物
- menu snapshot artifact：`/mnt/artifacts/codex/menu-navigation-field-snapshot/20260427T092416`
- 页面审计脚本：`scripts/migration/business_fact_page_surface_audit_probe.py`
- 数据库：`sc_prod_sim`

## 6. 回滚
- commit：回退本批次提交。
- 方法：恢复上述模型描述/别名与 XML 视图后执行 `make mod.upgrade MODULE=smart_construction_core`，再执行 `make restart`。

## 7. 下一批次
- 目标：继续处理剩余缺口，优先收口 `历史用户权限` 是否应继续对真实业务用户可见，并处理组织架构原生视图英文标签或替换为业务配置专用视图。
- 前置条件：保持 `wutao` 作为真实业务用户验证样本；不要把平台配置管理员可见的追溯页面重新开放给普通业务角色。
