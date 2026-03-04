# Odoo 原生承载差距迭代计划（v2.6-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v1_2`

## 目标来源（评估报告映射）

v2.5 已完成 evidence guard 职责去重，但对 `grouped_governance_trend_consistency` 分节仍以字段布尔约束为主，缺少与源报告的强对齐校验。v2.6-mini 聚焦“结论消费可信度”增强：补齐 trend 分节的 report 对齐治理。

## 本轮目标（执行项）

1. `contract_evidence_guard.py` 增加 trend 分节的源报告可读性与字段对齐校验
2. 增加 trend markdown 报告标题校验与 report pair（一致目录/同 stem）校验
3. 同步 `contract_evidence_guard_baseline.json` 的默认策略开关
4. 完成 grouped bundle + frontend quick gate + contract preflight（fast 参数）回归

## 验收口径

1. evidence trend 分节不仅校验字段存在，还校验与源报告一致
2. trend report 的 json/md 路径与文档标题满足治理策略
3. 以下命令通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`
