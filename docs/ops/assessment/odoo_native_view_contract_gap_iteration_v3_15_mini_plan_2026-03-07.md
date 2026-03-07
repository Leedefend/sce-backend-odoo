# Odoo 原生承载差距迭代计划（v3.15-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 目标定位

继续契约本体增强（非治理）。本轮聚焦可观测性落地：将 grouped 窗口身份与指纹状态暴露到前端 HUD，便于现场诊断与回放排障。

## 本轮目标

1. ActionView HUD 增加 `group_window_id`
2. ActionView HUD 增加 `group_query_fp`
3. ActionView HUD 增加 `route_group_fp`
4. grouped runtime guard 增加新状态标记约束
5. 完成回归与提交

## 验收口径

1. HUD 可直接看到当前窗口身份、服务端指纹、路由指纹
2. grouped runtime guard 可检测该能力未被误删
3. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `make verify.contract.preflight`
