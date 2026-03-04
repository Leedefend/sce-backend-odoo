# Odoo 原生承载差距迭代计划（v1.6-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v1_2`

## 目标来源（评估报告映射）

v1.5 已完成 grouped governance brief 的趋势策略化，但 evidence 侧仍缺少“与源报告一致性”的强约束。v1.6-mini 聚焦 evidence-source 对齐治理，防止导出链路出现静默漂移。

## 本轮目标（执行项）

1. `contract_evidence_guard.py` 增加 grouped governance brief 与 `report_json` 源报告对齐校验
2. baseline policy 增加对齐策略开关与 ratio 容差阈值
3. 完成 grouped bundle + frontend quick gate + contract preflight（fast 参数）回归

## 验收口径

1. evidence 中 `grouped_governance_brief` 与源报告字段保持一致（策略开启时）
2. `governance_coverage_ratio` 与源报告 ratio 一致（容差可配置）
3. 以下命令通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`
