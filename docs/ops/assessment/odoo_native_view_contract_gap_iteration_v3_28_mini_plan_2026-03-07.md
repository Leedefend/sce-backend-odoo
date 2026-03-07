# Odoo 原生承载差距迭代计划（v3.28-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 目标定位

继续契约本体增强（非治理）。本轮聚焦 `window_identity` 分组维度自描述：新增 `group_by_field`，使 identity 对象可独立标识分组上下文。

## 本轮目标

1. `window_identity` 新增 `group_by_field`
2. schema 同步新增 identity 分组维度字段
3. grouped smoke/guard 增加 `group_by_field` 与 flat 对齐校验
4. grouped 契约文档补齐 identity 分组维度定义
5. 完成回归与提交

## 验收口径

1. `window_identity.group_by_field` 与 `group_paging.group_by_field` 对齐
2. smoke/guard 可拦截字段缺失或漂移
3. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `make verify.contract.preflight`
