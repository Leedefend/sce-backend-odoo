# Menu Navigation Live Snapshot Batch 20260427

## 1. 本轮变更
- 目标：验证 `/api/menu/navigation` live 输出已携带菜单解释器新增字段。
- 完成：
  - 使用 `sc_demo / demo_pm` 登录真实 HTTP route。
  - 导出并校验 `nav_explained.flat/tree`。
  - 确认所有检查节点均包含 `scene_key`、`native_action_id`、`native_model`、`native_view_mode`、`confidence`、`compatibility_used`。
- 未完成：未新增正式 Make target；本批为一次性 live snapshot 验证。

## 2. 影响范围
- 模块：`/api/menu/navigation` live verification
- 启动链：否
- contract/schema：否，本批只验证上批加性字段
- default_route：否
- 前端：否

## 3. 风险
- P0：无，未改业务代码。
- P1：HTTP route 初次验证失败，因为运行中的 Odoo 尚未加载 Python 改动；已通过 `make restart` 收敛。
- P2：`verify.menu.scene_resolve.container` 仍暴露 2 个非本批字段类残余菜单。

## 4. 验证
- `make verify.menu.scene_resolve.container DB_NAME=sc_demo E2E_LOGIN=wutao E2E_PASSWORD=demo`：FAIL，账号密码错误。
- `make verify.menu.scene_resolve.container DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo`：FAIL，2 个 unresolved 菜单：
  - `smart_construction_core.menu_sc_project_quick_create`
  - `smart_construction_demo.menu_sc_project_list_showcase`
- `DB_NAME=sc_demo make odoo.shell.exec` 同源服务链 snapshot：PASS，artifact=`/mnt/artifacts/codex/menu-navigation-snapshot/20260427T030937Z`
- HTTP `/api/menu/navigation` 首次 snapshot：FAIL，missing=55；原因是 Odoo 服务未重启，仍加载旧 Python 代码。
- `make restart`：PASS。
- HTTP `/api/menu/navigation` 重跑：PASS，artifact=`artifacts/codex/menu-navigation-http-snapshot/20260427T031333`

## 5. 产物
- live HTTP summary：`artifacts/codex/menu-navigation-http-snapshot/20260427T031333/summary.json`
- live HTTP payload：`artifacts/codex/menu-navigation-http-snapshot/20260427T031333/nav_explained.json`
- service-chain snapshot：`artifacts/codex/menu-navigation-snapshot/20260427T030937Z/summary.json`
- auxiliary menu scene smoke：`artifacts/codex/portal-menu-scene-resolve/20260427T030859/menu_scene_resolve.json`

## 6. 回滚
- 方法：无需回滚本批验证产物；如需撤回上一批字段，回退 `MenuTargetInterpreterService` 与对应测试改动后重启 Odoo。
- 数据/升级：无需 `-u`，无数据回滚。

## 7. 下一批次
- 目标：把 `/api/menu/navigation` 字段校验固化为正式 Make target / verify script，避免后续靠一次性 node 片段验证。
- 前置条件：确认是否允许新增验证脚本与 Make target。
