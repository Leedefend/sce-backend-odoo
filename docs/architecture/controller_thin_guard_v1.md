# Controller Thin Guard v1

## Purpose

`verify.arch.controller_thin_guard` 审计 `addons/smart_core/controllers` 的 route 方法是否保持“协议适配层”薄化边界。

## Guard Dimensions

- `over_threshold`
  - route 方法行数超过 `max_method_lines`（当前 `80`）
- `orm_hints`
  - route 方法内出现 ORM 直读提示（例如 `request.env[`）

## Strict Fail-Gate

从 `1556` 起，该 guard 为严格门禁：

- 若 `over_threshold_count == 0` 且 `orm_hint_count == 0`
  - `status=PASS`
  - 退出码 `0`
- 否则
  - `status=FAIL`
  - 退出码 `2`

## Artifact

- `artifacts/architecture/controller_thin_guard_audit_v1.json`

关键摘要字段：

- `summary.controller_route_method_count`
- `summary.over_threshold_count`
- `summary.orm_hint_count`
- `over_threshold`
- `orm_hints`

## Current Baseline (2026-04-09)

- `over_threshold_count=0`
- `orm_hint_count=0`

## Operating Rule

- 若 guard 失败：先修 route 方法薄化，再重新运行 guard。
- 禁止通过放宽阈值或删除审计项绕过失败。

