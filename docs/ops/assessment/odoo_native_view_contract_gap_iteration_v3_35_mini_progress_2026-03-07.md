# Odoo 原生承载差距迭代进展（v3.35-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_5`

## 已完成

1. e2e grouped 语义签名增强：
   - 新增 `supports_window_nav_match`
2. grouped consistency guard 同步增强：
   - 新增字段结构校验、类型校验
   - grouped rows 命中时，导航一致性必须为 `true`
   - `consistency_score` 合法区间从 `[0,13]` 扩展到 `[0,14]`
3. baseline 刷新：
   - `scripts/verify/baselines/e2e_grouped_rows_signature.json` 已更新

## 验证结果

1. `make verify.grouped.governance.bundle`：PASS
2. `make verify.frontend.quick.gate`：PASS
3. `make verify.contract.preflight`：PASS

## 指标变化

在 `project_grouped` 场景下：

1. `consistency_score`：`13 -> 14`
2. `supports_window_nav_match`：`false -> true`

## 结论

本轮补齐了窗口导航语义的一致性验证，`window_identity` 与 `group_paging` 的运行态契约对齐能力进一步增强。
