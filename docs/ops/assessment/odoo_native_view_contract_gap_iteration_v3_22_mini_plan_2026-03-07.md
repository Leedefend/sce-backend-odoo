# Odoo 原生承载差距迭代计划（v3.22-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 目标定位

继续契约本体增强（非治理）。本轮聚焦窗口身份兼容层：为 `group_paging` 增加平铺字段 `window_key`，与 `window_identity.key` 等价，降低跨版本客户端接入成本。

## 本轮目标

1. 后端 `group_paging` 增加 `window_key`
2. schema 同步新增 `group_paging.window_key`
3. 前端 ActionView 读取 `window_identity.key` 并回退 `window_key`
4. smoke/guard 增加 `window_key` 与 `window_identity.key` 一致性校验
5. 完成回归与提交

## 验收口径

1. grouped 响应稳定返回 `window_key`
2. 前端在缺失 `window_identity.key` 时可回退到 `window_key`
3. smoke/guard 可检测 object/flat key 不一致
4. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `make verify.contract.preflight`
