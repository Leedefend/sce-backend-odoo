# Odoo 原生承载差距迭代计划（v3.13-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 目标定位

继续契约本体增强（非治理）。本轮聚焦 grouped 窗口过期保护：基于 `query_fingerprint` 识别路由窗口状态是否过期，并自动回到首窗口。

## 本轮目标

1. 路由接入 `group_fp`（grouped query fingerprint）
2. ActionView 在加载后比对 `route.group_fp` 与 `response.query_fingerprint`
3. 指纹不一致且 offset>0 时自动重置窗口（offset/page/collapsed）
4. 分组状态重置路径统一清理 `group_fp`
5. runtime guard 与文档补齐新语义

## 验收口径

1. 旧链接携带过期 `group_fp` 时不会停留在过期窗口
2. 当前查询指纹会被同步回 URL
3. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `make verify.contract.preflight`
