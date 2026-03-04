# Odoo 原生承载差距迭代计划（v3.1-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v2_8`

## 目标定位

继续执行“契约本体完善”，不新增治理项。本轮聚焦 grouped 分页响应语义可解释性：补齐请求偏移到实际偏移的契约表达。

## 本轮目标（执行项）

1. 后端 grouped_rows 增加分页偏移语义字段：
   - `page_requested_offset`
   - `page_applied_offset`
   - `page_max_offset`
2. 前端 schema 与消费同步：
   - schema 增加上述字段类型
   - ActionView 优先消费 `page_applied_offset`
3. 契约文档更新 grouped 分页字段定义
4. 完成 grouped bundle + frontend quick gate + contract preflight 回归

## 验收口径

1. grouped 分页契约能表达“请求偏移 vs 实际应用偏移 vs 可用上限”
2. 前端消费链路与新字段兼容并通过现有回归
3. 以下命令通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`
