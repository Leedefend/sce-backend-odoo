# Odoo 原生承载差距迭代计划（v1.5-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v1_2`

## 目标来源（评估报告映射）

v1.4 已补齐 grouped governance brief 的静态语义校验，但趋势治理仍较弱。v1.5-mini 聚焦 trend policy 化，确保 `has_previous=true` 时 delta 不可缺失，并可配置禁止关键指标回退。

## 本轮目标（执行项）

1. `grouped_governance_brief_baseline_guard.py` 增加 trend delta 强约束（按策略开关）
2. baseline policy 新增 `require_trend_delta_when_previous` 与多项回退开关
3. 完成 grouped bundle + frontend quick gate + contract preflight（fast 参数）回归

## 验收口径

1. `has_previous=true` 时，关键 delta 字段缺失将触发失败（在策略开启时）
2. 可按策略开启：
   - grouped e2e case count 回退禁止
   - grouped rows case count 回退禁止
   - grouped export marker hits 回退禁止
3. 以下命令通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`
