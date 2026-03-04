# Odoo 原生承载差距迭代计划（v1.9-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v1_2`

## 目标来源（评估报告映射）

v1.8 已对 `report_json/report_md` 做路径前后缀治理，但两者之间仍可能出现“分别合法、组合不一致”。v1.9-mini 聚焦 report pair 一致性治理，确保两条路径构成同一组审计产物。

## 本轮目标（执行项）

1. `contract_evidence_guard.py` 增加 report pair 一致性校验
2. baseline policy 增加 pair consistency 开关
3. 完成 grouped bundle + frontend quick gate + contract preflight（fast 参数）回归

## 验收口径

1. `grouped_governance_brief.report_json/report_md` 在策略开启时满足：
   - 同目录
   - 同 stem（仅后缀不同）
2. 以下命令通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`
