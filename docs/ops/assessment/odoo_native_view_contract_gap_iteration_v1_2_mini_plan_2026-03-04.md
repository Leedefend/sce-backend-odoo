# Odoo 原生承载差距迭代计划（v1.2-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v1_2`

## 目标来源（评估报告映射）

在 v1.0 已完成 grouped drift summary 与 grouped governance bundle 后，v1.2-mini 聚焦“治理简报分层化”：新增 grouped governance brief 审计件（report + schema + baseline），形成 grouped bundle 内的二级治理门。

## 本轮目标（执行项）

1. 新增 `grouped_governance_brief_guard`，聚合 `contract_governance_coverage` 与 `grouped_drift_summary` 信号
2. 新增 grouped governance brief schema guard 与 baseline guard
3. 将 grouped governance brief baseline guard 接入 `verify.grouped.governance.bundle`
4. 文档补充 grouped drift/gov 的诊断顺序与产物清单
5. 完成 grouped bundle + frontend quick gate + contract preflight（fast 参数）回归

## 验收口径

1. grouped governance brief 三层 guard 在 grouped governance bundle 中执行并通过
2. grouped governance brief 产物稳定输出：
   - `artifacts/grouped_governance_brief_guard.json`
   - `artifacts/grouped_governance_brief_guard.md`
3. 以下命令通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`
