# Odoo 原生承载差距迭代计划（v2.4-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v1_2`

## 目标来源（评估报告映射）

v2.3 已在 evidence guard 内实现 cross-report trend consistency，但校验逻辑集中在单脚本，复杂度继续上升。v2.4-mini 聚焦职责解耦：抽出独立 trend consistency guard 栈并接入 grouped bundle。

## 本轮目标（执行项）

1. 新增 `grouped_governance_trend_consistency` guard + schema + baseline
2. 新增对应 baseline 策略文件
3. 将 trend consistency baseline guard 接入 `verify.grouped.governance.bundle`
4. 文档补充 trend consistency 排障步骤与产物清单
5. 完成 grouped bundle + frontend quick gate + contract preflight（fast 参数）回归

## 验收口径

1. 生成并校验：
   - `artifacts/grouped_governance_trend_consistency_guard.json`
   - `artifacts/grouped_governance_trend_consistency_guard.md`
2. grouped bundle 包含 trend consistency baseline guard
3. 以下命令通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`
