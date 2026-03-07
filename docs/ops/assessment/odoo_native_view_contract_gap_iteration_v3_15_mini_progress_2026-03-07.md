# Odoo 原生承载差距迭代进展（v3.15-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 已完成

1. HUD 可观测性增强：
   - ActionView HUD 新增 `group_offset`
   - ActionView HUD 新增 `group_window_id`
   - ActionView HUD 新增 `group_query_fp`
   - ActionView HUD 新增 `route_group_fp`
2. runtime guard 同步：
   - grouped_rows_runtime_guard 增加 `groupWindowId/groupQueryFingerprint` 标记约束

## 验证结果

1. `make verify.grouped.governance.bundle`：PASS
2. `make verify.frontend.quick.gate`：PASS
3. `make verify.contract.preflight`：PASS

## 结论

grouped 契约的窗口身份语义已不仅可返回与校验，也可在前端诊断面直接观测，排障和回放定位效率提升。
