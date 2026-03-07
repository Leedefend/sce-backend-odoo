# Odoo 原生承载差距迭代进展（v3.33-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_5`

## 已完成

1. e2e grouped 语义签名增强：
   - 新增 `supports_window_identity_model`
   - 新增 `supports_window_identity_group_by`
2. grouped consistency guard 同步增强：
   - 新增字段结构校验、类型校验
   - grouped rows 命中时，新增两项必须为 `true`
   - `consistency_score` 合法区间从 `[0,9]` 扩展到 `[0,11]`
3. baseline 刷新：
   - `scripts/verify/baselines/e2e_grouped_rows_signature.json` 已更新

## 验证结果

1. `make verify.grouped.governance.bundle`：PASS
2. `make verify.frontend.quick.gate`：PASS
3. `make verify.contract.preflight`：PASS

## 指标变化

在 `project_grouped` 场景下：

1. `consistency_score`：`9 -> 11`
2. `supports_window_identity_model`：`false -> true`
3. `supports_window_identity_group_by`：`false -> true`

## 结论

本轮将 grouped e2e 从“窗口身份存在性验证”推进到“窗口身份与请求维度一致性验证”，契约语义可审计性进一步增强。
