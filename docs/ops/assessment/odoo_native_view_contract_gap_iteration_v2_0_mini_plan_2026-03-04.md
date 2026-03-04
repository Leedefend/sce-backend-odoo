# Odoo 原生承载差距迭代计划（v2.0-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v1_2`

## 目标来源（评估报告映射）

v1.9 已完成 grouped governance 报告路径与配对一致性治理，但缺少“策略全景可读视图”。v2.0-mini 聚焦 policy matrix 可审计化，将 grouped 相关基线策略聚合成统一报告并纳入 bundle。

## 本轮目标（执行项）

1. 新增 grouped governance policy matrix 导出脚本（JSON + MD）
2. 新增 policy matrix schema guard 与 baseline
3. 将 policy matrix schema guard 接入 `verify.grouped.governance.bundle`
4. 完成 grouped bundle + frontend quick gate + contract preflight（fast 参数）回归

## 验收口径

1. 生成并校验：
   - `artifacts/grouped_governance_policy_matrix.json`
   - `artifacts/grouped_governance_policy_matrix.md`
2. `verify.grouped.governance.bundle` 中包含 policy matrix 校验步骤
3. 以下命令通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`
