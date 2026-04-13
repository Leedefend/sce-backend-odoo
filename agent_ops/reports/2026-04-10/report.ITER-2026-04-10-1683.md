# ITER-2026-04-10-1683 Report

## Batch
- Batch: `P1-Batch12`
- Mode: `implement`
- Stage: `menu api envelope unification`

## Architecture declaration
- Layer Target: `Backend API controller envelope layer`
- Module: `smart_core platform menu api`
- Module Ownership: `addons/smart_core/controllers`
- Kernel or Scenario: `kernel`
- Reason: 统一菜单接口传输包裹，去除 Odoo `type=json` 自动 JSON-RPC 外层，确保前端按自定义契约直读。

## Change summary
- Updated `addons/smart_core/controllers/platform_menu_api.py`
  - `/api/menu/tree` route type: `json -> http`
  - `/api/user_menus` route type: `json -> http`
  - `/api/menu/navigation` route type: `json -> http`
  - Added explicit JSON response helper `_json_response(...)`
  - Added explicit HTTP status on auth/bad-request error envelope (401/400)
  - Navigation payload now reads from `request.jsonrequest` in http route mode

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1683.yaml` ✅
- `rg -n "/api/menu/tree|/api/user_menus|/api/menu/navigation" addons/smart_core/controllers/platform_menu_api.py` ✅
- `python3 -m py_compile addons/smart_core/controllers/platform_menu_api.py` ✅
- `make restart` ✅

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 风险点：
  - 菜单接口从 JSON-RPC 包裹切换为裸 JSON，依赖旧包裹形态的消费端会受影响。
- 缓释：
  - 前端已存在兼容解包逻辑（可同时处理 rpc/plain），不阻塞当前链路。

## Rollback suggestion
- `git restore addons/smart_core/controllers/platform_menu_api.py`

## Next suggestion
- 浏览器重新登录后抓取 `/api/menu/navigation`，确认响应顶层为 `ok/nav_fact/nav_explained/meta`（无 `jsonrpc/result`）。
