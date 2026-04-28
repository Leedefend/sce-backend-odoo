# Menu Navigation Verify Target Batch 20260427

## 1. 本轮变更
- 目标：把 `/api/menu/navigation` 字段校验固化为正式 verify target。
- 完成：
  - 新增 `scripts/verify/menu_navigation_field_snapshot.js`。
  - 新增 Make target：`verify.menu.navigation_snapshot`。
  - 新增 Make target：`verify.menu.navigation_snapshot.container`。
  - 校验字段：`scene_key`、`native_action_id`、`native_model`、`native_view_mode`、`confidence`、`compatibility_used`。
- 未完成：未处理 `verify.menu.scene_resolve.container` 暴露的 2 个 owner-signal 残余菜单。

## 2. 影响范围
- 模块：`scripts/verify`、`Makefile`
- 启动链：否
- contract/schema：否
- default_route：否
- 前端：否

## 3. 风险
- P0：无，未改运行时代码。
- P1：容器 target 产物由容器用户写入，host target 若复用同一 artifact 子目录可能遇到权限问题；host 可通过 `ARTIFACTS_DIR=...` 覆盖。
- P2：该 target 只校验字段形态与 scene/compat 基本一致性，不替代 owner-signal 深度审计。

## 4. 验证
- `node --check scripts/verify/menu_navigation_field_snapshot.js`：PASS
- `git diff --check -- Makefile scripts/verify/menu_navigation_field_snapshot.js`：PASS
- `make -n verify.menu.navigation_snapshot.container DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo`：PASS
- `make verify.menu.navigation_snapshot.container DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo`：PASS，trace=`bab73e1b7f68`
- `make verify.menu.navigation_snapshot DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo BASE_URL=http://127.0.0.1:8070 ARTIFACTS_DIR=artifacts/codex-host`：PASS，trace=`561faa29014c`

## 5. 产物
- container artifact：`artifacts/codex/menu-navigation-field-snapshot/20260427T031649`
- host artifact：`artifacts/codex-host/codex/menu-navigation-field-snapshot/20260427T031923`

## 6. 回滚
- 方法：删除 `scripts/verify/menu_navigation_field_snapshot.js`，并移除 Makefile 中新增的两个 target。
- 数据/升级：无需 `-u`，无数据回滚。

## 7. 下一批次
- 目标：处理 owner-signal 残余菜单，先审计 `smart_construction_core.menu_sc_project_quick_create` 与 `smart_construction_demo.menu_sc_project_list_showcase` 是否应降级、豁免或补 scene owner signal。
- 前置条件：明确 demo/showcase 菜单是否应继续出现在受约束的 scene resolve 检查范围。
