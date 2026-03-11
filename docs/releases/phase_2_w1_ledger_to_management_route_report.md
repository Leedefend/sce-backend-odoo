# SCEMS v1.0 Phase 2 W1：项目台账到控制台链路梳理

## 1. 结论
- 状态：`DONE`（W1-05）
- `projects.ledger -> project.management` 目标链路在配置与场景侧已存在。

## 2. 链路证据

| 链路环节 | 证据 |
|---|---|
| 项目台账场景存在 | `scene_registry.py` / `sc_scene_orchestration.xml` 中 `projects.ledger` |
| 项目管理场景存在 | `scene_registry.py` / `project_management_scene.xml` 中 `project.management` |
| 控制台路由存在 | `project.management` 目标路由 `/s/project.management` |
| 导航策略覆盖 | `construction_pm_v1.nav_allowlist` 包含 `projects.ledger` 与 `project.management` |

## 3. 建议后续验证
- 在 Phase 2 细化一条专门的路由专项 verify（从 ledger 选择项目后进入 management 并携带 `project_id`）。

