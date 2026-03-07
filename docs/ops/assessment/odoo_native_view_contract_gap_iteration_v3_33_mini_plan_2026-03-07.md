# Odoo 原生承载差距迭代计划（v3.33-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_5`

## 评估输入

上一轮已补齐 `window_identity/window_key/window_span` 的 e2e 能力位。下一步继续增强契约本体可验证性：将 `window_identity` 与请求维度（model/group_by）的一致性纳入 e2e 签名。

## 本轮目标

1. e2e grouped 语义签名新增：
   - `supports_window_identity_model`
   - `supports_window_identity_group_by`
2. grouped consistency guard 同步新增字段约束与 grouped 命中时强约束
3. 刷新 e2e grouped baseline 并完成回归

## 验收口径

1. `project_grouped` 在有 grouped rows 时，`window_identity` 的 `model/group_by_field` 必须与请求对齐
2. grouped e2e `consistency_score` 覆盖新增维度并可稳定通过
3. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `make verify.contract.preflight`
