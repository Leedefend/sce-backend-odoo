# Odoo 原生承载差距迭代计划（v3.8-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 目标定位

继续契约本体增强（非治理）。本轮聚焦 grouped 窗口导航语义：后端直接回传上一窗口/下一窗口偏移，避免前端重复推导。

## 本轮目标

1. 响应契约 `group_paging` 新增 `next_group_offset`
2. 响应契约 `group_paging` 新增 `prev_group_offset`
3. meta 同步回传 `next_group_offset/prev_group_offset`
4. 前端 schema 同步新增字段
5. 契约文档补齐字段语义

## 验收口径

1. `has_more=true` 时 `next_group_offset` 为可直接请求的下一窗口偏移
2. 当前窗口非首屏时 `prev_group_offset` 可回退到上一窗口
3. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `make verify.contract.preflight`
