# Odoo 原生承载差距迭代计划（v3.2-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v2_8`

## 目标定位

继续执行契约本体增强，不扩展治理。本轮聚焦 grouped 分页裁剪语义可观测化：明确 page size 请求/应用与 offset 是否被裁剪。

## 本轮目标（执行项）

1. 后端 grouped_rows 增加：
   - `page_requested_size`
   - `page_applied_size`
   - `page_clamped`
2. 前端 schema 与消费同步：
   - schema 增加字段类型
   - ActionView 的服务端同步判断包含 `page_clamped`
3. 契约文档更新字段说明
4. 完成 grouped bundle + frontend quick gate + contract preflight 回归

## 验收口径

1. grouped 分页契约可表达“size 请求/应用”和“offset 裁剪是否发生”
2. 前端与新字段兼容，现有回归通过
3. 以下命令通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`
