# TEMP｜smart_construction_core 边界事实盘点（2026-04-05）

> 说明：本文件为 `scan` 阶段事实清单，仅记录仓内可验证结构与引用，不给出整改方案与结论判定。

## 1) 模块结构事实（目录级）

- 目标模块：`addons/smart_construction_core`
- 顶层包含以下边界相关目录：
  - `controllers/`
  - `handlers/`
  - `services/`
  - `orchestration/`
  - `security/`
  - `models/`
  - `views/`

## 2) 可执行入口事实（HTTP Controller）

- `controllers/*.py` 文件数：`17`
- `@http.route` 标注数量：`34`
- 路由分布（按文件计数，节选）：
  - `addons/smart_construction_core/controllers/ops_controller.py`：6
  - `addons/smart_construction_core/controllers/frontend_api.py`：5
  - `addons/smart_construction_core/controllers/pack_controller.py`：4
  - `addons/smart_construction_core/controllers/capability_catalog_controller.py`：3
  - `addons/smart_construction_core/controllers/scene_template_controller.py`：2
- 典型路由前缀（节选）：
  - `/api/login`、`/api/session/get`、`/api/menu/tree`
  - `/api/ops/*`
  - `/api/packs/*`
  - `/api/capabilities/*`
  - `/api/scenes/*`

## 3) Intent/Handle 事实（注册与处理器）

- `handlers/*.py` 文件数：`39`
- `core_extension.py` 内 `registry["..."] = ...Handler` 注册条目：`42`
- 注册意图名节选（来自 `core_extension.py`）：
  - `project.execution.*`
  - `project.dashboard.*`
  - `cost.tracking.*`
  - `payment.*`
  - `settlement.*`
  - `usage.*`、`telemetry.track`
  - `app.catalog`、`app.nav`、`app.open`

## 4) 治理/发布相关命名事实（仅命名与位置）

- 控制器命名与路由命名中存在以下集合：
  - `ops_controller.py`（`/api/ops/*`）
  - `pack_controller.py`（`/api/packs/*`）
  - `scene_template_controller.py`（含 export/import 相关路由）
- 模型中存在治理/注册相关命名：
  - `addons/smart_construction_core/models/support/pack_registry.py`（`sc.pack.registry`）
  - `addons/smart_construction_core/models/support/subscription.py`（`sc.ops.job`）

## 5) 跨模块引用事实（边界耦合线索）

- 在 `handlers/`、`core_extension.py` 中可见对 `smart_core` 的大量直接导入与依赖。
- 在部分处理器中可见对 `smart_construction_scene` 服务的直接导入，例如：
  - `addons/smart_construction_core/handlers/my_work_summary.py`
  - `addons/smart_construction_core/handlers/cost_tracking_enter.py`
- `core_extension.py` 中存在场景注册器导入（`smart_construction_scene.services.capability_registry`）。

## 6) 当前批次扫描边界

- 扫描范围仅限：`addons/smart_construction_core/**`
- 本批未进行：
  - 跨仓重扫
  - 架构归因结论
  - 方案设计与整改变更

## 7) 供下一阶段使用的事实锚点

- 若进入 `screen` 阶段，可围绕以下“已确认事实对象”分类：
  - HTTP 入口（controller）
  - Intent 注册与 handler
  - ops/pack/scene-template 命名族
  - 对 `smart_core` / `smart_construction_scene` 的直接导入面

