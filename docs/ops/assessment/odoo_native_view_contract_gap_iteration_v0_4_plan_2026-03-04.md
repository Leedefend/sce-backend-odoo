# Odoo 原生承载差距迭代计划（v0.4）

日期：2026-03-04  
分支：`feat/interaction-core-p1-v0_4`

## 目标来源（评估报告映射）

基于 `odoo_native_view_contract_gap_assessment_2026-03-03.md` 的 P1/P2 差距，本轮聚焦“列表分组交互可运营化”和“回归治理增强”，在不引入新业务契约的前提下提升交互承载稳定性。

## 本轮目标（执行项）

1. 分组分页交互升级
   - 将 grouped-list 从“上一页/下一页”升级为“页码 + 跳转 + 总页数”可读交互
2. 分组分页状态路由化
   - 将每组分页偏移量持久化到路由（`group_page`），支持刷新恢复与状态清理
3. 前端 smoke 增强
   - 在 `fe_tree_view_smoke` 增加 grouped 响应断言（`group_summary/grouped_rows`）
4. 治理 guard 增强
   - 扩展 `grouped_rows_runtime_guard` 覆盖 `group_page` 相关链路标记

## 验收口径

1. 分组区块显示“第 X / Y 页”和“跳转”入口，跳页生效且不破坏现有行点击/批量操作
2. 路由包含并恢复 `group_page`；数据重载后可清理无效分页状态
3. `python3 scripts/verify/grouped_rows_runtime_guard.py` 通过
4. `make verify.frontend.quick.gate` 通过
5. `make verify.portal.tree_view_smoke.container`（或等效 tree smoke）通过
