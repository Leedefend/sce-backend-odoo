# smart_core 平台最小能力面清单 v1

## 目标
- 冻结 `smart_core` 在不依赖行业模块时的最小可运行能力面。
- 为 boundary/provider 迭代提供固定验收基线。

## 分层基线关系
- Platform Baseline（本文件）：仅验证平台内核最小能力面。
- Portal Baseline（运行时交付层）：验证前端交付链路最小可渲染面（`workspace.home` 可打开、same-route 稳定、非空渲染）。
- Product Baseline（业务场景层）：验证产品场景闭环（如 `project.initiation` 创建与 contract 回传）。

三层关系：先过 Platform，再过 Portal，最后过 Product。

## Layer Target
- `Platform Layer`

## Affected Modules
- `addons/smart_core`
- `scripts/verify/*minimum_surface*`
- `Makefile`

## Reason
- 防止后续边界迁移将平台启动骨架（认证/初始化/导航/契约）下沉到行业模块。

## 平台最小能力面（Must Have）
- 认证与会话：`login`、`auth.logout`
- 初始化主链：`system.init`（含 `app.init`/`bootstrap` alias）
- 应用壳导航：`app.catalog`、`app.nav`、`app.open`
- 契约与元数据：`ui.contract`、`meta.describe_model`、`permission.check`
- 运行时信封：`ok/data/meta/trace_id(intent链路)` + `contract_version/schema_version`

## 允许增强，不允许替代
- 行业模块可覆盖或增强平台默认输出。
- 平台默认 fallback 必须始终存在，且在 owner-only/minimal 部署可运行。

## 禁止下沉项
- `app.catalog` / `app.nav` / `app.open` 的平台 fallback
- `system.init` 的最小启动 fallback
- `ui.contract` 的最小 envelope fallback
- 平台最小 role/context surface fallback

## owner-only / minimal 部署通过标准
- `login` 成功，返回最小会话 contract
- `system.init` 成功，返回最小启动 surface
- `app.catalog -> app.nav -> app.open` 全链路可用
- `ui.contract`/`meta.describe_model`/`permission.check` 可调用
- 不因行业模块缺失出现 500
- 平台模式侧栏导航仅包含 `workspace.home`（不得泄漏行业 scene 菜单）

## same-route 冻结规则
- `isSameRouteTarget()` 是信号，不是错误。
- 仅当「same-route 且不可渲染且无 fallback/redirect 且会进入空壳/死循环」时允许 error。

## Guard / Smoke 清单
- Guard-A0：`make verify.smart_core.minimum_surface.legacy_group_guard`
- Guard-A：`make verify.smart_core.minimum_surface.handler_guard`
- Guard-B：`make verify.smart_core.minimum_surface.contract_guard`
- Smoke-C：`make verify.smart_core.minimum_surface.owner_startup_smoke`
- Regression-D：`make verify.smart_core.minimum_surface.same_route_guard`
- Regression-E：`make verify.smart_core.minimum_surface.order_regression_guard`
- Regression-F：`make verify.smart_core.minimum_surface.app_open_regression_guard`
- Regression-G：`make verify.smart_core.minimum_surface.nav_isolation_guard`
- 聚合：`make verify.smart_core.minimum_surface`

### Guard-A0 约束
- `smart_core` handlers 的 `REQUIRED_GROUPS` 不允许引用 legacy `group_sc_*`。
- `smart_core` handlers 的 `REQUIRED_GROUPS` 不允许引用行业组前缀 `smart_construction_core.*`。
- legacy `group_sc_*` 仅保留于 `addons/smart_core/security/groups.xml` 兼容层（sunset 期间）。

## PR 评审四问（边界必答）
- 改动后 `smart_core` 脱离行业模块还能独立启动吗？
- 该能力属于平台最小面，还是行业增强？
- 若迁出，平台 fallback 仍在吗？
- owner-only + same-route 回归是否通过？
