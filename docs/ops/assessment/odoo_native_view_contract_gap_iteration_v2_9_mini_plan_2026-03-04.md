# Odoo 原生承载差距迭代计划（v2.9-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v2_8`

## 目标来源（评估报告映射）

v2.8 已完成 trend schema guard 的类型与路径治理，但 grouped governance 的 `brief_schema_guard` 与 `policy_matrix_schema_guard` 仍以“键存在校验”为主，缺少类型约束与路径格式约束的一致化治理。

## 本轮目标（执行项）

1. 增强 `grouped_governance_policy_matrix_schema_guard.py`：
   - 增加 summary 字段类型约束
   - 增加 trend.delta 类型约束（has_previous=true 条件下）
   - 增加 summary report 路径前后缀约束
2. 增强 `grouped_governance_brief_schema_guard.py`：
   - 增加 summary 字段类型约束
   - 增加 trend.delta 类型约束（has_previous=true 条件下）
   - 增加 inputs 报告路径后缀约束
3. 同步两个 schema baseline 的类型与路径规则
4. 完成 grouped bundle + frontend quick gate + contract preflight（fast 参数）回归

## 验收口径

1. grouped governance 三个 schema guard（brief/policy_matrix/trend）都具备类型与路径治理能力
2. has_previous 场景下，trend.delta 类型满足契约
3. 以下命令通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`
