# Odoo 原生承载差距迭代进展（v0.6-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v0_6`

## 本轮目标

延续 P2 治理增强，完成 scene coverage 的双层 guard 与 preflight 接线，并增强 grouped 语义摘要的抗回退能力。

## 已完成

1. 计划与提交节奏落盘
   - 新增 `v0.6-mini` 计划文档，明确约 10 个独立提交切片

2. scene coverage schema guard
   - 新增 `scripts/verify/scene_contract_coverage_schema_guard.py`
   - 校验 `scene_contract_coverage_brief` 产物结构与类型

3. scene coverage baseline guard
   - 新增 `scripts/verify/scene_contract_coverage_baseline_guard.py`
   - 新增 baseline：`scripts/verify/baselines/scene_contract_coverage_guard_baseline.json`
   - 校验关键阈值与拓扑/layer 最小覆盖

4. preflight 接线
   - Makefile 新增 `verify.contract.scene_coverage.guard`
   - `verify.contract.preflight` 从 brief 升级为 guard 级接入

5. grouped 语义摘要增强
   - `fe_tree_view_smoke` 的 `grouped_pagination_semantic_summary` 新增 `consistency` 区块
   - 新增字段：
     - `request_offset_matches_observed`
     - `request_offset_aligned_to_page_limit`
     - `first_group_offset_aligned_to_page_limit`
   - 同步 baseline：`scripts/verify/baselines/fe_tree_grouped_signature.json`

6. grouped 语义 drift guard
   - 新增 `scripts/verify/grouped_pagination_semantic_drift_guard.py`
   - 防止 `consistency` 与关键布尔字段结构回退

7. quick gate 接线
   - Makefile 新增 `verify.frontend.grouped_pagination_semantic_drift.guard`
   - 已纳入 `verify.frontend.quick.gate`

8. contract evidence guard 增强
   - `scripts/verify/contract_evidence_guard.py` 新增 `scene_contract_coverage` 必需段与阈值校验
   - baseline 扩展 `scripts/verify/baselines/contract_evidence_guard_baseline.json`

9. 契约能力增强（grouped 分页服务端语义）
   - `api.data(list)` 增加 grouped 分页输入能力：`group_page_offsets`
   - backend grouped_rows 输出新增分页语义字段：
     - `page_offset` / `page_limit`
     - `page_current` / `page_total`
     - `page_range_start` / `page_range_end`
   - 前端 `ActionView` 列表请求透传 `group_page_offsets`，并优先消费后端 `page_offset/page_limit`
   - tree smoke grouped 请求新增 `group_page_offsets` 键，基线同步更新
   - `grouped_rows_runtime_guard` 同步适配后端新签名标记

## 已完成验证（阶段性）

1. `make verify.contract.scene_coverage.brief`：通过
2. `python3 scripts/verify/scene_contract_coverage_schema_guard.py`：通过
3. `python3 scripts/verify/scene_contract_coverage_baseline_guard.py`：通过
4. `make verify.contract.scene_coverage.guard`：通过
5. `make verify.portal.tree_view_smoke.container`：通过
6. `python3 scripts/verify/grouped_pagination_semantic_drift_guard.py`：通过
7. `make verify.frontend.grouped_pagination_semantic_drift.guard`：通过
8. `python3 scripts/contract/export_evidence.py`：通过
9. `python3 scripts/verify/contract_evidence_guard.py`：通过
10. `python3 scripts/verify/grouped_rows_runtime_guard.py`：通过
11. `make verify.portal.tree_view_smoke.container`：通过
12. `make verify.frontend.quick.gate`：通过

## 变更清单（当前已落地）

1. `docs/ops/assessment/odoo_native_view_contract_gap_iteration_v0_6_mini_plan_2026-03-04.md`
2. `scripts/verify/scene_contract_coverage_schema_guard.py`
3. `scripts/verify/scene_contract_coverage_baseline_guard.py`
4. `scripts/verify/baselines/scene_contract_coverage_guard_baseline.json`
5. `scripts/verify/fe_tree_view_smoke.js`
6. `scripts/verify/baselines/fe_tree_grouped_signature.json`
7. `scripts/verify/grouped_pagination_semantic_drift_guard.py`
8. `scripts/verify/contract_evidence_guard.py`
9. `scripts/verify/baselines/contract_evidence_guard_baseline.json`
10. `Makefile`
11. `addons/smart_core/handlers/api_data.py`
12. `frontend/apps/web/src/views/ActionView.vue`
