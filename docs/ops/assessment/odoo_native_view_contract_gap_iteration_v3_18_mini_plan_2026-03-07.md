# Odoo 原生承载差距迭代计划（v3.18-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 目标定位

继续契约本体增强（非治理）。本轮聚焦 grouped 窗口摘要在路由层闭环：将 `window_digest` 映射为路由键 `group_wdg`，实现窗口内容漂移的前端回正。

## 本轮目标

1. ActionView 路由态新增 `group_wdg`
2. grouped 路由读写新增 `group_wdg` 同步
3. grouped 加载流程新增 `group_wdg` 与响应 `window_digest` 的失配回正逻辑
4. grouped runtime guard 增加 `group_wdg` 标记约束
5. 完成回归与提交

## 验收口径

1. grouped 非首窗口在 `group_wdg` 失配时自动回正到首窗口并重载
2. HUD 可观测 `route_group_wdg`
3. grouped runtime guard 可检测该能力未被误删
4. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `make verify.contract.preflight`
