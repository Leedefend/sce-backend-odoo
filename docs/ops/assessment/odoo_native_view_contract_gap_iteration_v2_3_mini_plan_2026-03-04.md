# Odoo 原生承载差距迭代计划（v2.3-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v1_2`

## 目标来源（评估报告映射）

v2.2 已完成 policy matrix 趋势化，但 grouped governance brief 的趋势尚未进入 evidence 且缺少与 matrix 的跨报告一致性约束。v2.3-mini 聚焦 cross-report trend consistency。

## 本轮目标（执行项）

1. `export_evidence.py` 增加 grouped governance brief trend 摘要字段
2. `contract_evidence_schema_guard` baseline 纳入 brief trend 键
3. `contract_evidence_guard` baseline + 脚本增加：
   - brief trend 类型与回退约束
   - brief 与 matrix `has_previous` 一致性约束
4. 完成 grouped bundle + frontend quick gate + contract preflight（fast 参数）回归

## 验收口径

1. evidence 中可见 grouped governance brief trend 摘要
2. cross-report trend consistency 策略生效
3. 以下命令通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`
