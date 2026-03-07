# Odoo 原生承载差距迭代进展（v3.32-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_5`

## 已完成

1. e2e grouped 语义签名增强：
   - 新增 `supports_window_identity`
   - 新增 `supports_window_key`
   - 新增 `supports_window_span`
   - 新增 `window_span_matches_range`
2. grouped consistency guard 同步增强：
   - 新增上述能力位的必备键校验、类型校验与 grouped 命中时强约束
   - `consistency_score` 合法区间从 `[0,5]` 扩展到 `[0,9]`
3. 后端契约实现修复：
   - 修复 `api_data(list)` 中 `effective_page_size` 先用后赋值问题
4. baseline 刷新：
   - `scripts/verify/baselines/e2e_grouped_rows_signature.json` 已更新为新签名结构

## 验证结果

1. `make verify.grouped.governance.bundle`：PASS
2. `make verify.frontend.quick.gate`：PASS
3. `make verify.contract.preflight`：PASS

## 指标变化

基于 `artifacts/grouped_drift_summary_guard.json`：

1. `e2e_grouped_rows_case_count`：`0 -> 1`
2. `e2e_max_consistency_score`：`2 -> 9`

## 结论

本轮已将 grouped e2e 从“仅基础分页能力探测”提升到“覆盖窗口身份契约能力探测”，并修复了后端分页身份构造中的赋值顺序缺陷。
