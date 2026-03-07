# Odoo 原生承载差距迭代计划（v3.24-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 目标定位

继续契约本体增强（非治理）。本轮聚焦 `window_identity` 范围自描述：补齐 `window_start/window_end`，降低外层 `group_paging` 依赖。

## 本轮目标

1. `window_identity` 新增 `window_start/window_end`
2. schema 同步新增范围字段
3. smoke/guard 增加 identity 范围字段形状与 flat 对齐校验
4. 契约文档补齐 identity 范围字段说明
5. 完成回归与提交

## 验收口径

1. grouped 响应 `window_identity` 含窗口范围字段
2. smoke 能检查范围字段存在且与 `group_paging.window_start/window_end` 一致
3. guards 能拦截字段缺失/类型漂移
4. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `make verify.contract.preflight`
