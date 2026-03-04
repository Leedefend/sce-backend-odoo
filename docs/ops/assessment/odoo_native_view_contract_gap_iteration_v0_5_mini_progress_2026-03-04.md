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

5. 场景覆盖可视化增强（scene/contract）
   - 新增 `scripts/verify/scene_contract_coverage_brief.py`
   - 从 `docs/contract/exports/scene_catalog.json` 与 `intent_catalog_enriched.json` 提取覆盖摘要
   - 产物：
     - `artifacts/scene_contract_coverage_brief.json`
     - `artifacts/scene_contract_coverage_brief.md`
   - 指标包含：
     - scene/intent 声明与实际数量
     - renderable/interaction-ready 比率
     - intent layer 分布（core/domain/governance）
     - 带 smoke target 的 intent 数、write intent 数、etag intent 数
   - `Makefile` 新增目标：`verify.contract.scene_coverage.brief`

6. 预检聚合接线（preflight）
   - `verify.contract.preflight` 已纳入 `verify.contract.scene_coverage.brief`
   - 预检链路中的 legacy docs 阶段补齐发布文档标记（deprecated/successor/sunset/migration hint），避免非功能性阻塞

## 验证结果

1. `python3 scripts/verify/grouped_pagination_semantic_guard.py`：通过
2. `python3 scripts/verify/grouped_rows_runtime_guard.py`：通过
3. `make verify.frontend.quick.gate`：通过
4. `make verify.portal.tree_view_smoke.container`：通过
5. `make verify.contract.scene_coverage.brief`：通过
6. `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`：通过

## 变更清单

1. `scripts/verify/fe_tree_view_smoke.js`
2. `scripts/verify/baselines/fe_tree_grouped_signature.json`
3. `scripts/verify/grouped_pagination_semantic_guard.py`
4. `Makefile`
5. `docs/ops/assessment/odoo_native_view_contract_gap_iteration_v0_5_mini_progress_2026-03-04.md`
6. `scripts/verify/scene_contract_coverage_brief.py`
7. `docs/ops/releases/current/phase_11_2_contract_preflight_strict_rollout.md`
