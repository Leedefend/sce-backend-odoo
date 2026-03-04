# Odoo 原生承载差距迭代计划（v2.1-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v1_2`

## 目标来源（评估报告映射）

v2.0 已新增 grouped governance policy matrix 并接入 bundle，但 phase11 evidence 尚未显式纳入该分节。v2.1-mini 聚焦“矩阵入总账”，让策略覆盖计数进入 evidence 主链并受 schema/policy 约束。

## 本轮目标（执行项）

1. `export_evidence.py` 增加 `grouped_governance_policy_matrix` 分节
2. `contract_evidence_schema_guard` baseline 增加 matrix section/key
3. `contract_evidence_guard` baseline + 脚本增加 matrix 策略校验
4. 完成 grouped bundle + frontend quick gate + contract preflight（fast 参数）回归

## 验收口径

1. evidence JSON/MD 出现 grouped governance policy matrix 分节
2. matrix 分节受 schema + policy 双约束
3. 以下命令通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`
