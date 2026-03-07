# Odoo 原生承载差距迭代计划（v3.32-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_5`

## 评估输入

来自 grouped drift 评估信号（`artifacts/grouped_drift_summary_guard.json`）的下一轮关注点：

1. grouped e2e 契约覆盖需要体现 `window_identity` 相关能力位
2. grouped e2e 语义签名需要更细粒度区分分页能力与窗口身份能力

## 本轮目标

1. 扩展 e2e grouped 语义签名，新增：
   - `supports_window_identity`
   - `supports_window_key`
   - `supports_window_span`
   - `window_span_matches_range`
2. 同步 grouped consistency guard 对新能力位的结构与语义校验
3. 修复 grouped paging 运行时中的 `effective_page_size` 赋值顺序缺陷
4. 刷新 e2e grouped baseline 并完成回归

## 验收口径

1. grouped e2e 签名可稳定表达窗口身份能力
2. grouped consistency guard 覆盖新能力位，且 grouped case 命中时必须成立
3. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `make verify.contract.preflight`
