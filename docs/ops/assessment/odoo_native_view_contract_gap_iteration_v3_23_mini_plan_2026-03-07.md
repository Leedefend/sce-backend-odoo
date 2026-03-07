# Odoo 原生承载差距迭代计划（v3.23-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 目标定位

继续契约本体增强（非治理）。本轮聚焦 `window_identity` 自描述能力：补齐窗口数字上下文（offset/limit/count），使 identity 对象在脱离外层字段时仍可独立校验。

## 本轮目标

1. `window_identity` 新增 `group_offset/group_limit/group_count`
2. schema 同步新增上述字段
3. grouped smoke/guard 新增 identity 数字字段形状与一致性校验
4. grouped 契约文档补齐 identity 数字字段说明
5. 完成回归与提交

## 验收口径

1. grouped 响应 `window_identity` 含窗口数字上下文
2. smoke 可检查 identity 数字字段存在且与外层 `group_paging` 对齐
3. guards 可拦截字段缺失/类型漂移
4. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `make verify.contract.preflight`
