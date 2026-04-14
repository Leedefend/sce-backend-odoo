# ITER-2026-04-13-1826 项目原生页面字段 registry 恢复

## 任务结论

- 结果：PASS
- 用户报错：`"project.project"."short_name" field is undefined`
- 层级：Odoo Runtime Registry Recovery
- 模块：smart_construction_core project.project registry and view metadata
- 范围：operation-only，不改模型、不改视图、不导入数据。

## 根因判断

代码与 Odoo shell registry 中已经存在 `project.project.short_name`，写入试导也能成功写入该字段。因此这次原生页面报错不是字段代码缺失，而是浏览器连接的长运行 Web 服务 registry/cache 没有刷新到升级后的字段集。

## 执行动作

- 创建恢复任务契约：`agent_ops/tasks/ITER-2026-04-13-1826.yaml`
- 只读字段检查：PASS
  - `registry_missing=[]`
  - `ir_model_fields_count=21`
  - `db_columns_count=21`
  - `db_columns_missing=[]`
- 模块升级：PASS
  - `CODEX_NEED_UPGRADE=1 ENV=dev DB_NAME=sc_demo make mod.upgrade MODULE=smart_construction_core`
- Web 服务重启：PASS
  - 先误用 `make dev.restart`，Makefile 无此 target，未产生状态改动。
  - 随后使用仓库实际 target：`ENV=dev DB_NAME=sc_demo make restart`
- 服务健康：PASS
  - `sc-backend-odoo-dev-odoo-1` 状态为 `healthy`
- 重启后字段复核：PASS
  - `registry_missing=[]`
  - `ir_model_fields_count=4` for spot check
  - `fields_get(short_name)` 返回 `type=char`

## 验证结果

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-13-1826.yaml`：PASS
- `ENV=dev DB_NAME=sc_demo make odoo.shell.exec` 字段物化检查：PASS
- `CODEX_NEED_UPGRADE=1 ENV=dev DB_NAME=sc_demo make mod.upgrade MODULE=smart_construction_core`：PASS
- `ENV=dev DB_NAME=sc_demo make restart`：PASS
- `ENV=dev DB_NAME=sc_demo make ps`：PASS，Odoo service healthy
- `ENV=dev DB_NAME=sc_demo make odoo.shell.exec` fields_get 检查：PASS
- `make verify.native.business_fact.static`：PASS

## 风险与用户侧动作

服务端字段面已经恢复。若浏览器仍报同一资产栈上的旧错误，刷新页面并清掉该页缓存即可；不需要再导入数据。

本批没有回滚数据库写入，也没有修改 30 条项目骨架记录。

## 下一步

请重新打开原生项目页面验证。如果还报错，需要抓取新的错误堆栈；若错误字段不是 `short_name`，应按新的字段名重新执行字段面检查。
