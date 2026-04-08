# ITER-2026-04-08-1368 Report

## Batch
- Batch: `1/1`

## Summary of change
- 修复原生登录后首跳依赖 `sc_project_workbench` 客户端 action 的脆弱路径。
- 在 `addons/smart_construction_core/views/web_login_views.xml` 中将登录默认重定向目标固定为稳定 `act_window`：
  - `smart_construction_core.action_sc_project_list`
- 同时调整优先级：当 `sc.login.custom_enabled` 开启时，优先使用稳定默认跳转，再回退 `request.params.redirect`。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-08-1368.yaml` ✅
- `CODEX_MODE=fast CODEX_NEED_UPGRADE=1 ENV=dev DB_NAME=sc_demo MODULE=smart_construction_core make mod.upgrade` ✅
- `ENV=dev DB_NAME=sc_demo make restart` ✅
- `docker exec sc-backend-odoo-dev-odoo-1 sh -lc "curl -s http://127.0.0.1:8069/web/login | grep -n 'name=\"redirect\"'"` ✅
  - 渲染结果：`/web#menu_id=296&action=484`（项目列表 act_window）

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：仅调整登录模板默认跳转语义，不涉及 ACL、财务语义、模型结构与安全规则。

## Rollback suggestion
- `git restore addons/smart_construction_core/views/web_login_views.xml`
- `CODEX_MODE=fast CODEX_NEED_UPGRADE=1 ENV=dev DB_NAME=sc_demo MODULE=smart_construction_core make mod.upgrade`
- `ENV=dev DB_NAME=sc_demo make restart`

## Next suggestion
- 请在浏览器执行一次强制刷新（`Ctrl+F5`）后重登验证。
- 若仍有老 hash 资源残留，清理浏览器站点缓存后再试。
