# Odoo 原生承载差距迭代计划（v1.4-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v1_2`

## 目标来源（评估报告映射）

v1.3 已将 grouped governance brief 纳入 phase11 evidence，但 guard 仅校验存在性与基础阈值。v1.4-mini 聚焦“语义一致性强化”：把 coverage 比值、计数边界、marker 边界纳入 evidence policy。

## 本轮目标（执行项）

1. `contract_evidence_guard.py` 增加 grouped governance brief 语义一致性检查
2. baseline policy 增加 coverage/marker 边界开关与阈值
3. 完成 grouped bundle + frontend quick gate + contract preflight（fast 参数）回归

## 验收口径

1. grouped governance brief 在 evidence guard 中新增以下约束：
   - `governance_covered_file_count <= governance_total_file_count`
   - `governance_coverage_ratio` 与 `covered/total` 一致
   - `grouped_export_marker_hits <= grouped_export_marker_total`
   - `grouped_export_marker_total >= 1`
2. 以下命令通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`
