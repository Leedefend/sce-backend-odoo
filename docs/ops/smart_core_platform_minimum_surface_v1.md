# smart_core 平台最小能力面清单 v1

## 目标
- 冻结 `smart_core` 在不依赖行业模块时的最小可运行能力面。
- 为 boundary/provider 迭代提供固定验收基线。

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

## same-route 冻结规则
- `isSameRouteTarget()` 是信号，不是错误。
- 仅当「same-route 且不可渲染且无 fallback/redirect 且会进入空壳/死循环」时允许 error。

## Guard / Smoke 清单
- Guard-A：`make verify.smart_core.minimum_surface.handler_guard`
- Guard-B：`make verify.smart_core.minimum_surface.contract_guard`
- Smoke-C：`make verify.smart_core.minimum_surface.owner_startup_smoke`
- Regression-D：`make verify.smart_core.minimum_surface.same_route_guard`
- 聚合：`make verify.smart_core.minimum_surface`

## PR 评审四问（边界必答）
- 改动后 `smart_core` 脱离行业模块还能独立启动吗？
- 该能力属于平台最小面，还是行业增强？
- 若迁出，平台 fallback 仍在吗？
- owner-only + same-route 回归是否通过？
