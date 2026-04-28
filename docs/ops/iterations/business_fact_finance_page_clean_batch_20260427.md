# Batch Business Fact Finance Page Clean

## 1. 本轮变更
- 目标：清理财务账款核心办理页中暴露给真实用户的历史迁移、旧系统、source/legacy 技术字段。
- 完成：
  - 费用/保证金、收款收入、收款发票台账、付款申请明细、结算单/结算调整、资金对账、融资借款、资金台账页面移除历史来源/历史锚点/旧系统来源分组。
  - 从列表、表单、搜索中移除 `legacy_*`、`source_origin`、`source_*`、`source_kind`、`invoiced_before_amount` 等非办理字段展示。
  - 将仍需保留的只读控制表达式改为依赖业务状态 `legacy_confirmed`，不再要求把 `source_origin` 放回视图。
- 未完成：`历史财务事实（内部）` 整组菜单、流程待办、合同/项目/成本页面仍有英文模型描述或迁移字段，需要后续按菜单域继续收口。

## 2. 影响范围
- 模块：`addons/smart_construction_core`
- 启动链：否
- contract：否
- 路由：否

## 3. 风险
- P0：无。
- P1：业务用户无法再从核心办理页直接按旧系统记录号检索；如需审计追踪，应进入迁移审计/内部事实页面。
- P2：字段仍保留在模型层，后续如果前端契约直接消费模型字段，需要继续通过契约治理隐藏。

## 4. 验证
- 命令：`python3 -m xml.etree` 等价标准库解析 8 个变更 XML 文件，结果 `XML_PARSE_OK`。
- 命令：`rg` 静态扫描 8 个变更视图，确认无显示字段 `<field name="legacy_*|source_origin|source_*|source_kind|invoiced_before_amount">`，无“历史/旧系统/历史迁移/历史锚点/历史来源”分组标签。
- 命令：`ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast CODEX_NEED_UPGRADE=1 COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make mod.upgrade MODULE=smart_construction_core`
- 命令：`ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make odoo.shell.exec < scripts/migration/business_fact_page_surface_audit_probe.py`
- 命令：`ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" E2E_LOGIN=wutao E2E_PASSWORD=123456 make verify.menu.navigation_snapshot.container`
- 结果：PASS；全量业务根审计问题数 `1213 -> 1104`，技术字段可见 `236 -> 181`，菜单快照 trace `7115e4dfb958`。

## 5. 产物
- audit：`/mnt/artifacts/migration/business_fact_page_surface_audit_probe_result_v1.json`
- e2e：`/mnt/artifacts/codex/menu-navigation-field-snapshot/20260427T085642`

## 6. 回滚
- commit：回退本批次提交。
- 方法：恢复 8 个视图文件后，重新执行 `make mod.upgrade MODULE=smart_construction_core` 并 `make restart`。

## 7. 下一批次
- 目标：收口 `历史财务事实（内部）` 和 `流程待办` 的真实用户可见性。
- 前置条件：确认迁移审计/内部事实页面应只给平台配置管理员或专用审计能力组，而不应给普通业务办理角色。
