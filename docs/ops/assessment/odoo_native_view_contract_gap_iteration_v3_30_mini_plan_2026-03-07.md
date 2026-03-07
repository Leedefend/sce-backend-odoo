# Odoo 原生承载差距迭代计划（v3.30-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 目标定位

继续契约本体增强（非治理）。本轮聚焦 `window_identity` 空窗语义：新增 `window_empty`，让 identity 对象可直接表达窗口是否为空。

## 本轮目标

1. `window_identity` 新增 `window_empty`
2. schema 同步新增 `window_identity.window_empty`
3. grouped smoke/guard 增加空窗语义与 flat 对齐校验
4. grouped 契约文档补齐 `window_empty` 定义
5. 完成回归与提交

## 验收口径

1. `window_identity.window_empty` 与 `group_count` 语义一致
2. smoke/guard 可检测空窗语义漂移
3. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `make verify.contract.preflight`
