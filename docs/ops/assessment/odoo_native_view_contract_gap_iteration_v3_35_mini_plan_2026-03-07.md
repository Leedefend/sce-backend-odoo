# Odoo 原生承载差距迭代计划（v3.35-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_5`

## 评估输入

继续提升 grouped `window_identity` 契约可审计性，本轮聚焦窗口导航语义：验证 identity 与 flat paging 的 `prev/next/has_more` 对齐。

## 本轮目标

1. e2e grouped 语义签名新增 `supports_window_nav_match`
2. grouped consistency guard 同步新增字段约束与 grouped 命中时强约束
3. 刷新 e2e grouped baseline 并完成回归

## 验收口径

1. grouped rows 命中时，`window_identity.prev_group_offset/next_group_offset/has_more` 与 `group_paging` 一致
2. grouped e2e `consistency_score` 覆盖新增导航语义
3. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `make verify.contract.preflight`
