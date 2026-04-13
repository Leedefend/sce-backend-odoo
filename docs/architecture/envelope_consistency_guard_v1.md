# Envelope Consistency Guard v1

## Purpose

`verify.contract.envelope_consistency_guard` 用于审计 `addons/smart_core/controllers` 中 **API 路由** 的响应壳一致性，防止 controller 输出壳回退。

## Scope

- 仅纳入 decorator 中包含 `"/api/"` 的 route 方法。
- `website/non-api` 路由不作为该 guard 的 candidate 来源。

## Required Envelope Keys

本地 `_ok/_fail` 壳需要覆盖以下键：

- `ok`
- `data`
- `error`
- `meta`
- `effect`

## Envelope Shape Classification

每个 controller 文件会被标记为以下形态之一：

- `local_unified_v1`
  - 本地 `_ok/_fail` 已满足 required keys。
- `delegated_envelope`
  - 使用 `make_json_response` / `build_error_envelope`，或 route return 委托到标准 envelope helper。
- `local_legacy_or_unknown`
  - 使用 `make_response` 但未识别到标准壳。
- `no_envelope_signal`
  - API route 存在，但未识别到 envelope 信号。
- `no_route`
  - 文件无 route。

## Strict Fail-Gate

从 `1542` 起，此 guard 为严格门禁：

- 当 `inconsistent_candidate_count == 0`：
  - 产物 `status=PASS`
  - 进程退出码 `0`
- 当 `inconsistent_candidate_count > 0`：
  - 产物 `status=FAIL`
  - 进程退出码 `2`

## Artifact

产物固定输出：

- `artifacts/architecture/envelope_consistency_audit_v1.json`

关键摘要字段：

- `summary.files_with_routes`
- `summary.files_with_api_routes`
- `summary.inconsistent_candidate_count`
- `summary.required_envelope_keys`
- `inconsistent_candidates`

## Operating Notes

- 若 guard 失败，优先检查 candidate 是否为真实 API 入口；
- 若为委托模式，补充 delegation signal 识别；
- 仅在证据明确时新增 shape 分类，避免过度放宽门禁。
