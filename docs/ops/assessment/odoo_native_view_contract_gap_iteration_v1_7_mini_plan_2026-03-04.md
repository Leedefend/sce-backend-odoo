# Odoo 原生承载差距迭代计划（v1.7-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v1_2`

## 目标来源（评估报告映射）

v1.6 已实现 grouped governance brief 的 JSON 源报告对齐治理。v1.7-mini 补齐 markdown 侧治理，确保 evidence 指向的 `report_md` 也具备可读性和标题语义约束。

## 本轮目标（执行项）

1. `contract_evidence_guard.py` 增加 grouped governance brief `report_md` 对齐校验
2. baseline policy 增加 markdown 对齐开关与标题约束
3. 完成 grouped bundle + frontend quick gate + contract preflight（fast 参数）回归

## 验收口径

1. evidence 中 `grouped_governance_brief.report_md` 必须可读
2. markdown 报告必须包含治理标题（策略可配）
3. 以下命令通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`
