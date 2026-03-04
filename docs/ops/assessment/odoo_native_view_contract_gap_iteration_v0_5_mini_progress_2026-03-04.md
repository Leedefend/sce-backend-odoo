# Odoo 原生承载差距迭代进展（v0.5-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v0_5`

## 本轮目标

基于评估报告 P2 治理项，补齐 grouped 分页语义产物与轻量回归 guard，形成可持续验证闭环。

## 已完成

1. FE tree smoke 增强（grouped 分页语义摘要）
   - `fe_tree_view_smoke.js` 新增 `grouped_pagination_semantic_summary` 产物块
   - 摘要覆盖：
     - offset 归一公式与页码公式
     - 字段类型约束（`page_limit/page_offset/current_page/total_pages/range_start/range_end`）
     - 请求态（`request_offset` 与 `normalized_request_offset`）
     - 首组观测（是否存在、页码区间、offset 与 page_limit 对齐状态）
   - `summary.md` 同步增加分页语义关键行（normalized offset、首组页码信息）

2. grouped 分页语义基线更新
   - 更新 `scripts/verify/baselines/fe_tree_grouped_signature.json`
   - 版本升级为 `v0_5_mini`，新增分页语义摘要结构

3. 新增轻量 guard
   - 新增 `scripts/verify/grouped_pagination_semantic_guard.py`
   - 校验点：
     - smoke 脚本中语义摘要链路标记存在
     - baseline 中分页语义摘要结构完整
     - 关键字段类型稳定（`number/boolean`）

4. 快速门禁接线
   - `Makefile` 新增目标：`verify.frontend.grouped_pagination_semantic.guard`
   - 已接入 `verify.frontend.quick.gate`

## 验证结果

1. `python3 scripts/verify/grouped_pagination_semantic_guard.py`：通过
2. `python3 scripts/verify/grouped_rows_runtime_guard.py`：通过
3. `make verify.frontend.quick.gate`：通过
4. `make verify.portal.tree_view_smoke.container`：通过

## 变更清单

1. `scripts/verify/fe_tree_view_smoke.js`
2. `scripts/verify/baselines/fe_tree_grouped_signature.json`
3. `scripts/verify/grouped_pagination_semantic_guard.py`
4. `Makefile`
5. `docs/ops/assessment/odoo_native_view_contract_gap_iteration_v0_5_mini_progress_2026-03-04.md`
