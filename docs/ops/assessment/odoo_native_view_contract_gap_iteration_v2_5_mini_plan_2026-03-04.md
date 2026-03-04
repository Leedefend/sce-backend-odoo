# Odoo 原生承载差距迭代计划（v2.5-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v1_2`

## 目标来源（评估报告映射）

v2.4 已抽出独立 trend consistency guard，但 `contract_evidence_guard` 仍保留重复的 trend 细粒度规则。v2.5-mini 聚焦职责去重：evidence guard 改为消费 trend consistency guard 结论。

## 本轮目标（执行项）

1. `export_evidence.py` 增加 `grouped_governance_trend_consistency` 分节
2. `contract_evidence_schema_guard` baseline 增加该分节键约束
3. `contract_evidence_guard` baseline + 脚本调整：
   - 关闭重复 trend 细粒度规则默认开关
   - 增加对 trend consistency 分节的结论型约束
4. 完成 grouped bundle + frontend quick gate + contract preflight（fast 参数）回归

## 验收口径

1. evidence 总账包含 grouped governance trend consistency 分节
2. evidence guard 以独立 trend consistency guard 结论为主责
3. 以下命令通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`
