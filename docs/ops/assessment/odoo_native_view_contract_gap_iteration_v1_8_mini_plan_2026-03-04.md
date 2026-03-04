# Odoo 原生承载差距迭代计划（v1.8-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v1_2`

## 目标来源（评估报告映射）

v1.7 已完成 grouped governance brief 的 JSON/MD 可读与标题一致性治理。v1.8-mini 补齐路径规范治理，防止 evidence 指向路径发生目录/后缀漂移。

## 本轮目标（执行项）

1. `contract_evidence_guard.py` 增加 grouped governance brief report 路径前缀/后缀策略校验
2. baseline policy 增加 report_json/report_md 的 prefix/suffix 约束
3. 完成 grouped bundle + frontend quick gate + contract preflight（fast 参数）回归

## 验收口径

1. `grouped_governance_brief.report_json` 与 `report_md` 满足策略定义的 prefix/suffix 约束
2. 路径规范与可读性/语义校验并行生效
3. 以下命令通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`
