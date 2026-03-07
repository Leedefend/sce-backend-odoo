# Odoo 原生承载差距迭代计划（v3.19-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 目标定位

继续契约本体增强（非治理）。本轮聚焦 grouped 窗口身份字段标准化：在 `group_paging` 中新增对象化 `window_identity`，统一承载 `window_id/query_fingerprint/window_digest`。

## 本轮目标

1. 后端 `group_paging` 新增 `window_identity` 对象
2. 前端 ActionView 优先消费 `window_identity`，兼容旧平铺字段
3. schema 与契约文档补齐 `window_identity` 定义
4. grouped smoke/guard 增加 identity object 存在性与一致性校验
5. 完成回归与提交

## 验收口径

1. grouped 响应包含 `group_paging.window_identity`
2. 前端读取 `window_identity` 后 grouped 漂移防护行为不变
3. smoke/guard 能检测 object 形态缺失或与平铺字段不一致
4. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `make verify.contract.preflight`
