# 数据库策略 v1.0（Smart Construction / Odoo17）

## 目标
- 开发迭代与演示/生产隔离，避免 schema 污染
- 分支级数据库隔离，保证可复现与可回滚
- 一键初始化/重置/升级/seed

## 数据库分类与命名
- DEV：`sc_dev`
- DEV-Branch：`sc_dev__<branch_slug>`
- DEMO/UAT：`sc_demo`
- CI：`sc_ci`
- PROD：`sc_prod`
- `sc_odoo`：Postgres 初始化默认库（不用于日常开发迭代）

## 连接参数
- DB_HOST=db（compose 内）
- DB_USER=odoo
- DB_PASSWORD=odoo

## 分支 ↔ DB 绑定
- 修改模型/视图/ACL/菜单：必须使用 `sc_dev__<branch_slug>`

## 操作规范
- 开发升级：`odoo -d <DB> -u smart_construction_core --stop-after-init`
- DEV 可重置；DEMO 里程碑同步；PROD 严格发布流程

## dbfilter 现状与切换
- 当前 `.env`：`ODOO_DBFILTER=^(sc_odoo|sc_demo)$`（仅允许基线/演示库）
- 若需开发/分支库，需将 dbfilter 放宽为：`^(sc_odoo|sc_demo|sc_dev|sc_dev__.*)$` 并重启 odoo

