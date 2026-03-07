# Odoo 原生承载差距迭代进展（v3.10-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 已完成

1. smoke 验证增强：
   - `fe_tree_view_smoke.js` 新增 `group_offset=5` 回放请求
   - 新增 `grouped_offset_replay_summary`，覆盖 request/response/consistency
2. 守卫增强：
   - `grouped_pagination_semantic_guard.py` 增加 offset 回放摘要结构与类型校验
   - `grouped_pagination_semantic_drift_guard.py` 增加 offset 回放一致性校验
   - `grouped_contract_consistency_guard.py` 增加 smoke marker 约束
3. 基线同步：
   - `fe_tree_grouped_signature.json` 更新为包含 `grouped_offset_replay_summary`
4. 契约文档补充：
   - grouped contract 明确前端应优先消费后端 `next_group_offset/prev_group_offset`

## 验证结果

1. `TREE_GROUPED_SNAPSHOT_UPDATE=1 DB_NAME=sc_demo BASE_URL=http://localhost:8070 node scripts/verify/fe_tree_view_smoke.js`：PASS
2. `make verify.grouped.governance.bundle`：PASS
3. `make verify.frontend.quick.gate`：PASS
4. `make verify.contract.preflight`：PASS

## 结论

grouped `group_offset` 深链回放语义已具备可执行、可审计、可漂移拦截的验证闭环，后续契约升级可在 CI 中稳定防回归。
