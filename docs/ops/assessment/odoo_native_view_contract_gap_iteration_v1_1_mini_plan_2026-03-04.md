# Odoo 原生承载差距迭代计划（v1.1-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v1_1`

## 目标来源（评估报告映射）

在 v1.0 完成 grouped 治理闭环后，v1.1-mini 聚焦“治理结果可消费化”：把 grouped 治理汇总输出为统一 artifact，供 release 审核和后续自动化读取。

## 本轮目标（执行项）

1. 新增 grouped governance brief 导出脚本（JSON + MD）
2. 新增 grouped governance brief schema guard
3. 新增 grouped governance brief baseline guard
4. 接入 `verify.grouped.governance.bundle`
5. 文档补充 grouped governance brief 的用途与排障顺序
6. 完成 quick gate + preflight 回归并更新进展文档

## 验收口径

1. 产物存在：
   - `artifacts/grouped_governance_brief.json`
   - `artifacts/grouped_governance_brief.md`
2. brief schema/baseline guard 均通过
3. 以下命令通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`
