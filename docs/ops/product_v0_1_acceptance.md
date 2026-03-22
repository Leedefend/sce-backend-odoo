# Product v0.1 Acceptance

## Acceptance Goal
- 确认当前生命周期系统已经达到第一个可交付产品标准。

## Functional Acceptance
- 可从 `project.initiation.enter` 连续进入 `project.dashboard.enter`。
- 可从 dashboard 连续进入 `project.plan_bootstrap.enter`。
- 可从 plan 连续进入 `project.execution.enter`。
- 可执行 `project.execution.advance` 并看到状态变化。

## Contract Acceptance
- `system.init` 维持 `boot / preload / runtime` 分层。
- 四个产品场景保持 `entry(minimal) + runtime blocks + suggested_action`。
- `execution.advance` 返回 `success/blocked + reason_code + suggested_action + from_state/to_state`。

## Odoo Acceptance
- `execution_tasks` 数据来自 `project.task`。
- 执行推进成功或阻塞结果写入 `project.project` chatter。
- 执行推进后生成最小 follow-up `mail.activity`。

## Verification Entry Points
- `make verify.system_init.latency_budget DB_NAME=sc_platform_core E2E_LOGIN=admin E2E_PASSWORD=admin`
- `make verify.portal.preload_runtime_surface DB_NAME=sc_platform_core E2E_LOGIN=admin E2E_PASSWORD=admin`
- `make verify.frontend.typecheck.strict`
- `make verify.frontend.product.contract_consumption.guard`
- `make verify.product.project_dashboard_baseline DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin`
- `make verify.phase12b.baseline PLATFORM_DB_NAME=sc_platform_core PLATFORM_LOGIN=admin PLATFORM_PASSWORD=admin PORTAL_DB_NAME=sc_platform_core PORTAL_LOGIN=admin PORTAL_PASSWORD=admin PRODUCT_DB_NAME=sc_demo PRODUCT_LOGIN=admin PRODUCT_PASSWORD=admin E2E_LOGIN=admin E2E_PASSWORD=admin`

## Acceptance Threshold
- preload latency budget 通过。
- 产品全链 smoke 通过。
- 前端契约消费 guard 通过。
- 不存在将 runtime 重数据回灌到 `system.init` 的回退。
