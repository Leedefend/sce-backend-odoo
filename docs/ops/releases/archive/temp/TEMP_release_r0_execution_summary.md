# TEMP Release R0 Execution Summary

Last updated: 2026-02-06
Branch: `codex/release-r0-nav-closure`
Scope: R0-1 / R0-2 / R0-3 / R0-4

## Completion Checklist

- [x] R0-1 目录菜单不再默认落到 Workbench
- [x] R0-2 Workbench 降级为异常页语义
- [x] R0-3 登录后默认进入有意义页面（`projects.list`）
- [x] R0-4 官方首发 Package 命名与范围定型

## What Was Implemented

1. 目录菜单自动下钻（first reachable child）
- resolver 增加 `redirect` 结果类型，支持优先命中首个可达 `action_id` 或 `scene_key`。
- `MenuView` 新增 `redirect` 处理：
  - 目标是 action -> 跳转 `/a/:actionId?menu_id=:menuId`
  - 目标是 scene -> 跳转 `/s/:sceneKey?menu_id=:menuId`

2. Workbench 异常页化
- 标题、文案由功能入口语义改为异常语义。
- 新增明确出口：
  - `Back to home` -> `/s/projects.list`
  - `Open menu` -> 打开首个可达菜单（若无则回 `/s/projects.list`）
- tiles 仅在 `CAPABILITY_MISSING` 场景展示。

3. 首发成功路径固化
- 登录默认跳转从 `/` 改为 `/s/projects.list`。
- 根路由 `/` 重定向到 `/s/projects.list`。
- 非 admin 访问 admin 页时回退到 `/s/projects.list`。

4. 首发 Package 定型文档
- 新增 R0 发布基线文档，明确：
  - Package key: `sc-project-execution-core`
  - Display name: `智能施工 · 项目执行管理（基础版）`
  - Channel: `stable`
  - 首发场景：`projects.list`, `projects.ledger`, `projects.intake`(optional)

## Changed Files

- `frontend/apps/web/src/app/resolvers/menuResolver.ts`
- `frontend/apps/web/src/app/resolvers/menuResolverCore.js`
- `frontend/apps/web/src/views/MenuView.vue`
- `frontend/apps/web/src/views/WorkbenchView.vue`
- `frontend/apps/web/src/router/index.ts`
- `frontend/apps/web/src/views/LoginView.vue`
- `frontend/apps/web/src/layouts/AppShell.vue`
- `scripts/verify/fe_menu_no_action_smoke.js`
- `docs/ops/releases/release_r0_launch_package.md`

## Verification

Passed:
- `node scripts/verify/fe_menu_no_action_smoke.js`

Known existing repo debt (not introduced by this change):
- `npm run typecheck` fails in unrelated files:
  - `src/components/view/ViewFieldRenderer.vue`
  - `src/components/view/ViewRelationalRenderer.vue`
  - `src/pages/ModelFormPage.vue`
  - `src/views/ActionView.vue`
  - `src/views/RecordView.vue`

## R0 Definition of Done Status

- [x] 目录菜单不再落到 Workbench（默认路径）
- [x] Workbench 仅作为异常入口
- [x] 登录后 30 秒内可进入有意义页面（默认 `projects.list`）
- [x] 官方首发 Scene Package 命名完成
- [ ] 主观体验项待你最终验收：“打开系统不再有空心感”

## Notes

- 当前文档为 TEMP 汇总，便于 release 收口跟踪；后续可并入正式 release note。
