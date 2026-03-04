# Odoo 原生承载差距迭代计划（v2.8-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v2_8`

## 目标来源（评估报告映射）

v2.7 已补强 trend baseline guard，但 trend schema guard 仍主要做“键存在 + 顶层类型”校验，缺少 summary 字段类型约束与 report 路径格式约束。v2.8-mini 聚焦 schema 层契约精度提升。

## 本轮目标（执行项）

1. 增强 `grouped_governance_trend_consistency_schema_guard.py`：
   - 增加 summary 字段类型校验（bool/int/number）
   - 增加 report json/md 路径前后缀校验
2. 同步 `grouped_governance_trend_consistency_schema_guard.json` baseline：
   - 增加 `summary_key_types`
   - 增加 report 路径规则
3. 完成 grouped bundle + frontend quick gate + contract preflight（fast 参数）回归

## 验收口径

1. trend schema guard 能对 summary 关键字段做类型级治理
2. trend report 路径满足 artifacts 产物命名契约
3. 以下命令通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`
