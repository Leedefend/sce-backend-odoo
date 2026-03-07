# Odoo 原生承载差距迭代进展（v3.34-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_5`

## 已完成

1. e2e grouped 语义签名增强：
   - 新增 `supports_window_identity_algo`
   - 新增 `supports_window_identity_key_tuple`
2. grouped consistency guard 同步增强：
   - 新增字段结构校验、类型校验
   - grouped rows 命中时，上述两项必须为 `true`
   - `consistency_score` 合法区间从 `[0,11]` 扩展到 `[0,13]`
3. baseline 刷新：
   - `scripts/verify/baselines/e2e_grouped_rows_signature.json` 已更新

## 验证结果

1. `make verify.grouped.governance.bundle`：PASS
2. `make verify.frontend.quick.gate`：PASS
3. `make verify.contract.preflight`：PASS

## 指标变化

在 `project_grouped` 场景下：

1. `consistency_score`：`11 -> 13`
2. `supports_window_identity_algo`：`false -> true`
3. `supports_window_identity_key_tuple`：`false -> true`

## 结论

本轮完成窗口身份算法与 key tuple 的契约一致性验证，grouped e2e 签名对 `window_identity` 的可审计粒度进一步提升。
