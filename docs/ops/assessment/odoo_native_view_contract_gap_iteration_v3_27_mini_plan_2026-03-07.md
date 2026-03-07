# Odoo 原生承载差距迭代计划（v3.27-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 目标定位

继续契约本体增强（非治理）。本轮聚焦 `window_identity` 分页参数自描述：补齐 `page_size/has_group_page_offsets`，使 identity 对象可独立表达分页输入语义。

## 本轮目标

1. `window_identity` 新增 `page_size/has_group_page_offsets`
2. schema 同步新增对应字段
3. grouped smoke/guard 增加分页参数形状与 flat 对齐校验
4. grouped 契约文档补齐 identity 分页参数定义
5. 完成回归与提交

## 验收口径

1. `window_identity.page_size/has_group_page_offsets` 与 `group_paging` 对齐
2. smoke 能检查该语义未漂移
3. guards 能拦截字段缺失/类型漂移
4. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `make verify.contract.preflight`
