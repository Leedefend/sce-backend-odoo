# Odoo 原生承载差距迭代计划（v3.34-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_5`

## 评估输入

继续沿 grouped e2e 契约签名增强路线，将窗口身份从“字段存在/模型对齐”推进到“算法与 key tuple 可逆一致性”。

## 本轮目标

1. e2e grouped 语义签名新增：
   - `supports_window_identity_algo`
   - `supports_window_identity_key_tuple`
2. grouped consistency guard 同步新增字段约束与 grouped 命中时强约束
3. 刷新 e2e grouped baseline 并完成回归

## 验收口径

1. grouped rows 命中时，`window_identity.algo` 必须满足当前协定（`sha1`）
2. grouped rows 命中时，`window_identity.key` 必须与 `version/algo/window_id/window_digest` tuple 一致
3. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `make verify.contract.preflight`
