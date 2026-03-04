# Odoo 原生承载差距迭代计划（v3.3-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v2_8`

## 目标定位

继续契约本体增强（非治理）：提升 grouped 分页“请求参数与返回摘要”的契约表达，支持轻量客户端不解析全量 `grouped_rows` 也能掌握分页关键语义。

## 本轮目标（执行项）

1. 请求契约增强：`group_limit`
2. 响应契约增强：顶层 `group_paging`
3. grouped 行契约增强：
   - `page_requested_size`
   - `page_applied_size`
   - `page_requested_offset`
   - `page_applied_offset`
   - `page_max_offset`
   - `page_clamped`
4. 前端 schema 与消费同步
5. 契约文档同步

## 验收口径

1. grouped 分页请求/响应契约具备更完整的“请求值、应用值、裁剪状态、汇总摘要”表达
2. 保持向后兼容（`page_limit/page_offset` 仍可用）
3. 通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`
