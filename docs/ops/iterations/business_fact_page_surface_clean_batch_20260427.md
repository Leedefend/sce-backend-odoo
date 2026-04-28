# Batch Business Fact Page Surface Clean

## 1. 本轮变更
- 目标：先清理业务配置中定额页面的英文与来源字段暴露，并形成真实用户可见页面审计入口。
- 完成：
  - `sc_norm_engine` 定额专业、章节、子目、导入向导模型描述统一为中文。
  - 定额页面移除 `sheet_name`、`unit_raw`、`line_no` 等来源/导入字段显示，保留正式业务字段 `计量单位`。
  - 新增 `business_fact_page_surface_audit_probe.py`，按真实用户可见菜单扫描英文标签、技术字段、迁移/来源字段。
- 未完成：核心财务/合同/项目页面仍存在大量历史事实页、英文模型描述和 legacy/source 字段，进入下一批按菜单域收口。

## 2. 影响范围
- 模块：`addons/sc_norm_engine`、`scripts/migration`
- 启动链：否
- contract：否
- 路由：否

## 3. 风险
- P0：无。
- P1：定额子目的导入来源单位不再直接显示，若历史数据未完成 `uom_id` 映射，页面可能缺少单位展示。
- P2：审计脚本默认按 `wutao` 与智能施工业务根扫描，其他角色需通过 `AUDIT_LOGIN` 扩展验证。

## 4. 验证
- 命令：`python3 -m py_compile addons/sc_norm_engine/models/norm_specialty.py addons/sc_norm_engine/wizard/norm_import_wizard.py scripts/migration/business_fact_page_surface_audit_probe.py`
- 命令：`ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast CODEX_NEED_UPGRADE=1 COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make mod.upgrade MODULE=sc_norm_engine`
- 命令：`ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" make odoo.shell.exec < scripts/migration/business_fact_page_surface_audit_probe.py`
- 命令：`ENV=test ENV_FILE=.env.prod.sim COMPOSE_BIN="docker compose" COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim CODEX_MODE=fast COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod-sim.yml" E2E_LOGIN=wutao E2E_PASSWORD=123456 make verify.menu.navigation_snapshot.container`
- 结果：PASS；定额页面专项复核 `SC_NORM_SURFACE_ROWS=[]`；全量业务根审计仍为 `business_page_surface_gap_present`。

## 5. 产物
- audit：`/mnt/artifacts/migration/business_fact_page_surface_audit_probe_result_v1.json`
- e2e：`/mnt/artifacts/codex/menu-navigation-field-snapshot/20260427T084713`
- trace：`c0e0acaae7aa`

## 6. 回滚
- commit：回退本批次提交。
- 方法：恢复 `sc_norm_engine` 视图/模型描述后，重新执行 `make mod.upgrade MODULE=sc_norm_engine` 并 `make restart`。

## 7. 下一批次
- 目标：按 `财务账款` 优先清理业务页面中的 `历史/legacy/source` 字段与英文模型描述。
- 前置条件：确认“历史财务事实（内部）”是否应对真实业务用户隐藏，只保留给平台/迁移审计角色。
