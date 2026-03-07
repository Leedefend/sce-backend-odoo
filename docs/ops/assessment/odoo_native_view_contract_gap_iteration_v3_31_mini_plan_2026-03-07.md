# Odoo 原生承载差距迭代计划（v3.31-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 目标定位

继续契约本体增强（非治理）。本轮聚焦 `window_identity` 窗口跨度语义：新增 `window_span`，让 identity 对象直接表达 `window_start/window_end` 对应窗口长度。

## 本轮目标

1. `window_identity` 新增 `window_span`
2. schema 同步新增 `window_identity.window_span`
3. grouped smoke/guard 增加窗口跨度语义与 flat 对齐校验
4. grouped 契约文档补齐 `window_span` 定义
5. 完成回归与提交

## 验收口径

1. `window_identity.window_span` 与 `window_start/window_end/group_count` 语义一致
2. smoke/guard 可检测窗口跨度语义漂移
3. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `make verify.contract.preflight`
