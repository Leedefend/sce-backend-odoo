# Odoo 原生承载差距迭代计划（v3.26-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 目标定位

继续契约本体增强（非治理）。本轮聚焦 `window_identity` 总量自描述：补齐可选字段 `group_total`，在开启 `need_group_total` 时 identity 对象可独立表达总量语义。

## 本轮目标

1. `window_identity` 增加可选 `group_total`
2. schema 同步新增 `window_identity.group_total`
3. grouped smoke/guard 增加 `group_total` 形状与 flat 对齐校验
4. grouped 契约文档补齐 `group_total` 可选语义
5. 完成回归与提交

## 验收口径

1. `need_group_total=true` 时，`window_identity.group_total` 与 `group_paging.group_total` 一致
2. `need_group_total=false` 时，不要求该字段存在
3. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `make verify.contract.preflight`
