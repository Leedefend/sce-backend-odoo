# Odoo 原生承载差距迭代计划（v1.0-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v1_0`

## 目标来源（评估报告映射）

在 v0.9 已完成 grouped 契约一致性治理后，v1.0-mini 聚焦“证据可审计闭环”：把 grouped 关键语义同时写入 smoke/e2e/evidence 三层，并形成一条统一的 drift 汇总检查。

## 本轮目标（执行项）

1. 新增 grouped drift summary guard，聚合 fe_tree/e2e/evidence 的关键字段一致性
2. quick gate 接入 grouped drift summary guard
3. contract evidence markdown 增加 grouped consistency 小结段
4. e2e grouped baseline 增加 `consistency_score`（布尔能力位汇总）
5. 文档补充 grouped drift 诊断与排障路径
6. 完成 tree smoke + frontend quick gate + e2e.contract + contract preflight

## 验收口径

1. grouped drift summary guard 在 quick gate 中执行并通过
2. evidence JSON/MD 能看见 grouped consistency 汇总
3. 以下命令通过：
   - `make verify.portal.tree_view_smoke.container`
   - `make verify.frontend.quick.gate`
   - `make verify.e2e.contract`
   - `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`
