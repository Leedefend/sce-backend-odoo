# Batch-Business-Fact-Projection-Page-Surface

## 1. 本轮变更
- 目标：继续清理真实业务用户可见页面，优先收口审计中高集中度的资金日报、资金日报明细、融资台账、物料档案/分类、采购/一般合同页面。
- 完成：
  - 资金日报、融资台账底层迁移字段保留在模型中，新增只读业务别名字段供页面展示，避免业务视图直接暴露 `source_*`、`legacy_*` 字段。
  - 资金日报明细移除旧系统来源分组、历史编号、附件引用、来源表等内部字段。
  - 物料档案/分类菜单、动作、视图统一去掉“历史”字样，页面只保留编码、名称、规格、单位、分类、项目、价格、产品提升等业务字段。
  - 采购/一般合同菜单、动作、视图统一去掉“历史”字样，移除项目/往来方历史编号和旧系统来源分组。
  - 为相关模型补充中文 `_description` 与字段 `string`，减少英文默认标签。
- 未完成：全量页面审计仍有 233 项缺口，集中在项目原生页、施工日志、付款执行、发票登记、综合合同、历史用户权限、组织架构等页面。

## 2. 影响范围
- 模块：`addons/smart_construction_core`
- 文件：
  - `models/support/legacy_fund_daily_snapshot_fact.py`
  - `models/support/legacy_fund_daily_line.py`
  - `models/support/legacy_financing_loan_fact.py`
  - `models/support/legacy_material_catalog.py`
  - `models/support/legacy_purchase_contract_fact.py`
  - `views/support/legacy_fund_daily_snapshot_views.xml`
  - `views/projection/fund_daily_views.xml`
  - `views/support/legacy_financing_loan_views.xml`
  - `views/support/legacy_material_catalog_views.xml`
  - `views/support/legacy_purchase_contract_views.xml`
- 启动链：否
- contract/schema：否
- default_route：否
- public intent：否

## 3. 风险
- P0：无已知 P0。本批次不迁移、不删除业务数据。
- P1：新增的只读业务别名字段是非存储计算字段，仅用于视图显示；若后续要排序/聚合，需要再评估是否改为存储字段。
- P2：底层模型仍以 `sc.legacy.*` 命名，属于历史数据承载事实；本批次只清理用户可见页面，不改模型真源。

## 4. 验证
- 命令：
  - `python3 -m py_compile addons/smart_construction_core/models/support/legacy_fund_daily_snapshot_fact.py addons/smart_construction_core/models/support/legacy_fund_daily_line.py addons/smart_construction_core/models/support/legacy_financing_loan_fact.py addons/smart_construction_core/models/support/legacy_material_catalog.py addons/smart_construction_core/models/support/legacy_purchase_contract_fact.py`
  - `XML_PARSE_OK for 5 changed XML files`
  - `git diff --check`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast CODEX_NEED_UPGRADE=1 COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make mod.upgrade MODULE=smart_construction_core`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make odoo.shell.exec < scripts/migration/business_fact_page_surface_audit_probe.py`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make restart`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" E2E_LOGIN=wutao E2E_PASSWORD=123456 make verify.menu.navigation_snapshot.container`
- 结果：
  - `business_fact_page_surface_audit` issue_count `508 -> 233`
  - `menu_issue_summary` 中 `资金日报`、`资金日报明细`、`融资台账`、`物料档案`、`物料分类`、`采购/一般合同` 已不再作为高集中缺口出现。
  - 导航快照：PASS，trace=`40b81db321c3`

## 5. 产物
- menu snapshot artifact：`/mnt/artifacts/codex/menu-navigation-field-snapshot/20260427T091756`
- 页面审计脚本：`scripts/migration/business_fact_page_surface_audit_probe.py`
- 数据库：`sc_prod_sim`

## 6. 回滚
- commit：回退本批次提交。
- 方法：恢复上述模型字段标签/别名和 XML 视图后执行 `make mod.upgrade MODULE=smart_construction_core`，再 `make restart`。

## 7. 下一批次
- 目标：继续处理剩余高集中页面，优先 `施工日志`、`发票登记`、`付款执行`、`综合合同`、`历史用户权限`，同时评估组织架构是否应使用自定义业务配置视图替代 Odoo 原生英文标签视图。
- 前置条件：保持 `wutao` 作为真实业务用户验证样本。
