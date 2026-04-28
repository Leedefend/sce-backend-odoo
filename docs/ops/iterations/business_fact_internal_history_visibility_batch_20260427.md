# Batch-Business-Fact-Internal-History-Visibility

## 1. 本轮变更
- 目标：将真实业务用户可见面中的内部历史迁移页面收口到平台配置管理员能力组，避免业务办理用户看到“历史/迁移/流程工作台”类内部页面。
- 完成：
  - `smart_construction_core` 财务历史事实中心及其子菜单改为仅 `group_sc_cap_config_admin` 可见。
  - `流程待办`、`流程工作台` 改为仅 `group_sc_cap_config_admin` 可见，业务用户不再通过财务能力组进入内部流程迁移视图。
  - 对相关 `ir.actions.act_window.groups_id` 使用 `(6, 0, [...])` 替换旧财务组授权。
  - 对相关 `ir.ui.menu.groups_id` 增加显式替换记录，避免 Odoo 升级时 menuitem groups 追加导致旧组残留。
- 未完成：真实业务页面仍有 508 项页面显示缺口，下一批继续清理资金日报、资金日报明细、融资台账、历史物料、历史采购合同等页面。

## 2. 影响范围
- 模块：`addons/smart_construction_core`
- 文件：
  - `views/support/legacy_finance_internal_views.xml`
  - `views/support/history_todo_views.xml`
  - `views/support/legacy_invoice_runtime_views.xml`
  - `views/support/legacy_file_index_views.xml`
  - `views/support/legacy_expense_deposit_views.xml`
  - `views/support/legacy_invoice_tax_views.xml`
- 启动链：否
- contract/schema：否
- default_route：否
- public intent：否

## 3. 风险
- P0：无已知 P0。本批次不删除模型、字段或数据，只调整动作/菜单可见能力组。
- P1：平台配置管理员仍可访问内部历史事实页面；这是预期边界，用于迁移追溯和配置核查。
- P2：若未来新增历史迁移菜单但未显式替换 `groups_id`，可能重新被业务能力组看到；后续需继续用页面审计脚本守住真实用户可见面。

## 4. 验证
- 命令：
  - `XML_PARSE_OK for 6 changed XML files`
  - `rg group_sc_cap_finance_*/group_sc_internal_user in changed internal history XML files`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast CODEX_NEED_UPGRADE=1 COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make mod.upgrade MODULE=smart_construction_core`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make odoo.shell.exec` with `WUTAO_INTERNAL_HISTORY_MENUS` probe
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make odoo.shell.exec < scripts/migration/business_fact_page_surface_audit_probe.py`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make restart`
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" E2E_LOGIN=wutao E2E_PASSWORD=123456 make verify.menu.navigation_snapshot.container`
- 结果：
  - `WUTAO_INTERNAL_HISTORY_MENUS={"count": 0, "login": "wutao", "menus": []}`
  - 抽样菜单组：`menu_sc_finance_history_center`、`menu_sc_history_todo`、`menu_sc_history_todo_all`、`menu_sc_legacy_receipt_income_fact` 均仅剩 `smart_construction_core.group_sc_cap_config_admin`
  - `business_fact_page_surface_audit` issue_count `1104 -> 508`
  - 导航快照：PASS，trace=`8b3ac9f5461e`

## 5. 产物
- menu snapshot artifact：`/mnt/artifacts/codex/menu-navigation-field-snapshot/20260427T090837`
- 页面审计脚本：`scripts/migration/business_fact_page_surface_audit_probe.py`
- 数据库：`sc_prod_sim`

## 6. 回滚
- commit：回退本批次提交。
- 方法：恢复上述 XML 中的 action/menu groups 后执行 `make mod.upgrade MODULE=smart_construction_core`，再 `make restart` 清理运行时缓存。

## 7. 下一批次
- 目标：继续真实业务页面清理，优先处理 `资金日报`、`资金日报明细`、`融资台账` 中仍暴露的英文字段、legacy/source 字段和非业务字段。
- 前置条件：保持 `wutao` 作为真实业务用户验证样本，业务配置管理员权限不等同于平台配置管理员权限。
