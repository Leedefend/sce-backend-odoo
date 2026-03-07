# Odoo 原生承载差距迭代计划（v3.12-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 目标定位

继续契约本体增强（非治理）。本轮聚焦 grouped 窗口身份语义：为窗口增加可追踪身份与查询指纹，支持跨端一致性判断。

## 本轮目标

1. `group_paging` 新增 `window_id`
2. `group_paging` 新增 `query_fingerprint`
3. meta 新增 `group_window_id/group_query_fingerprint`
4. schema 与前端消费状态同步
5. 文档补齐字段定义

## 验收口径

1. grouped 响应提供稳定窗口身份与查询指纹
2. 前端可读取并记录这两个字段
3. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `make verify.contract.preflight`
