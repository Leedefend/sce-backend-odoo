# Odoo 原生承载差距迭代进展（v3.14-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 已完成

1. smoke 签名增强：
   - `fe_tree_view_smoke.js` 新增 `grouped_identity_summary`
   - 输出 `window_id/query_fingerprint` 及一致性字段
2. baseline 更新：
   - `fe_tree_grouped_signature.json` 同步 identity 摘要
3. 守卫增强：
   - `grouped_pagination_semantic_guard.py` 增加 identity 摘要结构与类型校验
   - `grouped_pagination_semantic_drift_guard.py` 增加 identity 一致性布尔校验
   - `grouped_contract_consistency_guard.py` 增加 identity smoke marker 与一致性校验

## 验证结果

1. `TREE_GROUPED_SNAPSHOT_UPDATE=1 DB_NAME=sc_demo BASE_URL=http://localhost:8070 node scripts/verify/fe_tree_view_smoke.js`：PASS
2. `make verify.grouped.governance.bundle`：PASS
3. `make verify.frontend.quick.gate`：PASS
4. `make verify.contract.preflight`：PASS

## 结论

grouped 契约已形成“能力字段 + 消费保护 + 签名守卫”的闭环：窗口身份语义不仅可返回可消费，还可在基线与 guard 中持续防回归。
