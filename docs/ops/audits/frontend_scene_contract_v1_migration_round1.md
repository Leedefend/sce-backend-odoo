# 前端 `scene_contract_v1` 迁移阶段结论（Round 1）

## 阶段目标
- 将前端页面从仅消费 `page_orchestration_v1`，逐步迁移为优先消费后端场景编排主契约 `scene_contract_v1`。
- 保持兼容：若 `scene_contract_v1` 不可用，回退到现有 `page_orchestration_v1` 路径。

## 本轮已完成页面
- `home`（`frontend/apps/web/src/views/HomeView.vue`）
- `project.management.dashboard`（`frontend/apps/web/src/views/ProjectManagementDashboardView.vue`）
- `my_work`（`frontend/apps/web/src/views/MyWorkView.vue`）
- `workbench`（`frontend/apps/web/src/views/WorkbenchView.vue`）

## 本轮新增/升级守卫
- `verify.frontend.scene_contract_v1.consumption.guard`
  - 覆盖以上 4 个页面的 `scene_contract_v1` 消费主链 token。
- `verify.frontend.actionview.scene_specialcase.guard`
  - 持续约束 `ActionView` 不回退到 `scene/model` 硬编码特判。

## 验证结果
- `make verify.frontend.scene_contract_v1.consumption.guard` PASS
- `python3 scripts/verify/frontend_actionview_scene_specialcase_guard.py` PASS
- `make verify.frontend.typecheck.strict` PASS
- `make verify.page_orchestration.target_completion.guard` PASS
- `make verify.workspace_home.orchestration_schema.guard` PASS
- `make verify.project.dashboard.contract` PASS

## 剩余待迁移页面清单（下一阶段）

### P0（优先）
- `action`（`frontend/apps/web/src/views/ActionView.vue`）
  - 目标：统一走 `scene_contract_v1` 的 `zones[] + blocks{}` 自动渲染主链，继续压缩语义推断逻辑。
- `record`（`frontend/apps/web/src/views/RecordView.vue`）
  - 目标：将记录页交互入口（按钮、区域）从页面内推断迁移到契约驱动。

### P1（核心导航页）
- `scene`（`frontend/apps/web/src/views/SceneView.vue`）
- `menu`（`frontend/apps/web/src/views/MenuView.vue`）

### P2（辅助页）
- `scene_health`（`frontend/apps/web/src/views/SceneHealthView.vue`）
- `scene_packages`（`frontend/apps/web/src/views/ScenePackagesView.vue`）
- `usage_analytics`（`frontend/apps/web/src/views/UsageAnalyticsView.vue`）
- `placeholder`（`frontend/apps/web/src/views/PlaceholderView.vue`）
- `login`（`frontend/apps/web/src/views/LoginView.vue`，仅需要评估是否纳入统一契约消费）

## 边界说明
- 本轮不改 scene key / page key / route 协议。
- 本轮不改权限基线与业务判定逻辑。
- 仅做“前端消费路径”从旧契约到主契约的收敛。

## 阶段结论
- 已完成第一批高价值页面的 `scene_contract_v1` 主消费接入。
- 可以进入下一批（`ActionView` + `RecordView`）迁移。
