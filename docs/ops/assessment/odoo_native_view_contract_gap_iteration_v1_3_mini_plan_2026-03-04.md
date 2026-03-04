# Odoo 原生承载差距迭代计划（v1.3-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v1_2`

## 目标来源（评估报告映射）

v1.2 已新增 grouped governance brief guard 栈，但 phase11 evidence 尚未将该分节纳入 schema/policy 治理。v1.3-mini 聚焦证据总账闭环，把 grouped governance brief 从 bundle 能力提升为 evidence 强约束能力。

## 本轮目标（执行项）

1. `export_evidence.py` 增加 `grouped_governance_brief` 分节
2. `contract_evidence_schema_guard` baseline 增加 grouped governance brief 必要键
3. `contract_evidence_guard` baseline 增加 grouped governance brief 阈值策略
4. `contract_evidence_guard.py` 增加 grouped governance brief 校验逻辑
5. 完成 grouped bundle + frontend quick gate + contract preflight（fast 参数）回归

## 验收口径

1. evidence JSON/MD 出现 grouped governance brief 分节
2. grouped governance brief 被 schema + policy 双重约束
3. 以下命令通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`
