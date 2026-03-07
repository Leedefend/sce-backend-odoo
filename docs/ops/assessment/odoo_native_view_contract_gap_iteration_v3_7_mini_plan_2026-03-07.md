# Odoo 原生承载差距迭代计划（v3.7-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 目标定位

继续契约本体增强（非治理）。本轮聚焦 grouped 分页“总量可见性”：在不破坏默认性能路径的前提下，让客户端可按需拿到分组总数。

## 本轮目标

1. 请求契约新增 `need_group_total`（按需开关）
2. 响应契约 `group_paging` 新增 `group_total`
3. meta 新增 `need_group_total/group_total`
4. 前端 schema 与请求透传同步
5. 文档补齐 `group_total` 语义与触发条件

## 验收口径

1. 默认请求不计算分组总数（无额外开销）
2. `need_group_total=true` 时返回 `group_total`
3. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `make verify.contract.preflight`
