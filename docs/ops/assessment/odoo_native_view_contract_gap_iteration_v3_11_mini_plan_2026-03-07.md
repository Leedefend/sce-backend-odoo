# Odoo 原生承载差距迭代计划（v3.11-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 目标定位

继续契约本体增强（非治理）。本轮聚焦 grouped 窗口范围语义：后端回传当前分组窗口的 start/end，前端优先消费，减少本地推导。

## 本轮目标

1. `group_paging` 新增 `window_start/window_end`
2. meta 新增 `group_window_start/group_window_end`
3. schema 同步新增窗口范围字段
4. ActionView/GroupSummaryBar 优先展示后端窗口范围
5. 文档补齐字段定义

## 验收口径

1. 分组窗口摘要可直接显示后端返回的范围
2. 空窗口时范围为 `0-0`
3. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `make verify.contract.preflight`
