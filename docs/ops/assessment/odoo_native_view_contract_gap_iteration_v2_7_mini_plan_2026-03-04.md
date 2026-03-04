# Odoo 原生承载差距迭代计划（v2.7-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v1_2`

## 目标来源（评估报告映射）

v2.6 已补齐 `contract_evidence_guard` 对 trend consistency 分节的源报告对齐校验，但 trend guard 自身 baseline 仍偏轻量，缺少 report 路径治理与 has_previous 条件下 delta 类型的独立兜底。

## 本轮目标（执行项）

1. 强化 `grouped_governance_trend_consistency_baseline_guard.py`：
   - 新增 `has_previous_brief/has_previous_matrix` bool 类型约束
   - 新增 has_previous 条件下 delta 字段类型约束
2. 增加 trend report 路径治理：
   - `report.json` / `report.md` 前缀与后缀约束
3. 同步 `grouped_governance_trend_consistency_baseline_guard.json` 策略
4. 完成 grouped bundle + frontend quick gate + contract preflight（fast 参数）回归

## 验收口径

1. trend baseline guard 可独立约束 trend 报告路径与关键字段类型
2. has_previous 为 true 时 delta 字段类型满足契约
3. 以下命令通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`
