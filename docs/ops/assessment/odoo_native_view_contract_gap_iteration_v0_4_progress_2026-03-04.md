# Odoo 原生承载差距迭代进展（v0.4）

日期：2026-03-04  
分支：`feat/interaction-core-p1-v0_4`

## 本轮目标

基于评估报告（2026-03-03）中“交互承载与治理回归”差距，增强 grouped-list 的可运营分页能力，并补齐对应路由与验证闭环。

## 已完成

1. 分组分页交互升级
   - `ListPage` 分组区块新增“第 X / Y 页”信息与“跳转”操作
   - 保留“上一页/下一页”并与当前样本窗口一致

2. 分组分页状态路由化
   - `ActionView` 新增 `group_page` 路由状态（每组 offset 映射）
   - 分组切换、样本条数切换、无效分组清理时同步归一化 `group_page`
   - 刷新后可恢复每组分页偏移（在有效分组集合内）

3. 治理 guard 增强
   - `grouped_rows_runtime_guard` 增加 `group_page` 相关链路标记
   - 覆盖分页状态解析/序列化与分页交互入口

4. FE tree smoke 覆盖增强
   - `fe_tree_view_smoke` 新增 grouped 请求与产物记录（`group_summary/grouped_rows`）
   - 增加单层/双层 envelope 兼容解析
   - 默认记录 grouped 覆盖状态；`REQUIRE_GROUPED_ROWS=1` 时启用强断言

## 验证结果

1. `python3 scripts/verify/grouped_rows_runtime_guard.py`：通过
2. `make verify.frontend.quick.gate`：通过
3. `make verify.portal.tree_view_smoke.container`：通过

## 变更清单

1. `frontend/apps/web/src/views/ActionView.vue`
2. `frontend/apps/web/src/pages/ListPage.vue`
3. `scripts/verify/grouped_rows_runtime_guard.py`
4. `scripts/verify/fe_tree_view_smoke.js`
5. `docs/ops/assessment/odoo_native_view_contract_gap_iteration_v0_4_plan_2026-03-04.md`
