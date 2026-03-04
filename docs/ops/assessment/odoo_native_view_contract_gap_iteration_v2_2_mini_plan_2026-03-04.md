# Odoo 原生承载差距迭代计划（v2.2-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v1_2`

## 目标来源（评估报告映射）

v2.1 已将 policy matrix 接入 evidence，但缺少趋势维度治理。v2.2-mini 聚焦 policy matrix trend 化，并把 trend 回退约束纳入 evidence guard。

## 本轮目标（执行项）

1. `grouped_governance_policy_matrix.py` 增加 `has_previous + delta` 趋势字段
2. matrix schema guard baseline 增加 trend 字段约束
3. `export_evidence.py` 将 matrix trend 摘要接入 evidence
4. `contract_evidence_guard` baseline + 脚本增加 matrix trend 防回退约束
5. 完成 grouped bundle + frontend quick gate + contract preflight（fast 参数）回归

## 验收口径

1. policy matrix 报告包含 trend 与 delta（首次可为空，历史可比较）
2. evidence 中可见 matrix trend 摘要
3. trend 相关策略在 evidence guard 生效
4. 以下命令通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`
