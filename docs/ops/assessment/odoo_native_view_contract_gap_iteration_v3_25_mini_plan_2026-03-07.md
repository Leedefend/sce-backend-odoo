# Odoo 原生承载差距迭代计划（v3.25-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 目标定位

继续契约本体增强（非治理）。本轮聚焦 `window_identity` 导航自描述：补齐 `prev_group_offset/next_group_offset/has_more`，使 identity 对象可独立表达窗口前后关系。

## 本轮目标

1. `window_identity` 新增导航字段（prev/next/has_more）
2. schema 同步新增导航字段
3. grouped smoke/guard 新增导航字段形状与 flat 对齐校验
4. grouped 契约文档补齐 identity 导航字段说明
5. 完成回归与提交

## 验收口径

1. grouped 响应 `window_identity` 含导航字段
2. smoke 可检查导航字段存在且与 `group_paging` 对齐
3. guards 可拦截导航字段缺失/类型漂移
4. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `make verify.contract.preflight`
