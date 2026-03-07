# Odoo 原生承载差距迭代计划（v3.17-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 目标定位

继续契约本体增强（非治理）。本轮聚焦 grouped 窗口内容身份补强：在 `window_id/query_fingerprint` 基础上新增 `window_digest`，形成窗口身份与窗口内容双锚点。

## 本轮目标

1. 后端 `group_paging` 新增 `window_digest`
2. `ApiDataListResult` schema 新增 `group_paging.window_digest`
3. ActionView 读取并在 HUD 暴露 `group_window_digest`
4. grouped smoke/guard 同步新增 `window_digest` 语义校验
5. 完成回归与提交

## 验收口径

1. grouped 响应稳定返回 `group_paging.window_digest`（40位 hex）
2. 前端 HUD 可观测 `group_window_digest`
3. grouped semantic/runtime guards 可检测该字段未被误删
4. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `make verify.contract.preflight`
