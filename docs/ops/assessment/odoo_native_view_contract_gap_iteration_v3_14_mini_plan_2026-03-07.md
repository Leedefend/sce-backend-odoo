# Odoo 原生承载差距迭代计划（v3.14-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 目标定位

继续契约本体增强（非治理）。本轮聚焦验证闭环：将 grouped `window_id/query_fingerprint` 身份语义纳入 smoke 签名与 guard 强校验。

## 本轮目标

1. `fe_tree_view_smoke` 输出 `grouped_identity_summary`
2. baseline 同步记录 `window_id/query_fingerprint`
3. semantic guard 增加 identity 摘要结构/类型校验
4. drift/consistency guard 增加 identity 一致性校验
5. 回归验证并形成可审计证据

## 验收口径

1. baseline 包含 `grouped_identity_summary`
2. `has_window_id/has_query_fingerprint/query_fingerprint_hex` 均受 guard 约束
3. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `make verify.contract.preflight`
