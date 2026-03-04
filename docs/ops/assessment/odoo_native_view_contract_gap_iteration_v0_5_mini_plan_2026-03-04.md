# Odoo 原生承载差距迭代计划（v0.5-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v0_5`

## 目标来源（评估报告映射）

基于 `odoo_native_view_contract_gap_assessment_2026-03-03.md` 的 P2 治理项，先做一轮低风险、小步快跑的治理增强：

1. 场景覆盖可视化增强（scene/contract 快照覆盖状态可读）
2. grouped 分页语义回归固化（避免后续迭代回退）
3. 文档证据闭环（计划-进展-验证三件套）

## 本轮目标（执行项）

1. 为 FE tree smoke 产物增加 grouped 分页关键语义摘要字段（页偏移归一、页码信息）
2. 增加一个轻量 guard，校验 grouped 分页语义摘要字段存在且类型稳定
3. 更新进展文档并纳入一轮标准验证

## 验收口径

1. 新增/增强的 grouped 分页语义产物可在 artifacts 中稳定输出
2. 新 guard 通过，并在缺失字段时可明确报错
3. 以下命令通过：
   - `python3 scripts/verify/grouped_rows_runtime_guard.py`
   - `make verify.frontend.quick.gate`
   - `make verify.portal.tree_view_smoke.container`
