# Odoo 原生承载差距迭代计划（v3.16-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 目标定位

继续契约本体增强（非治理）。本轮聚焦 grouped 窗口身份在路由层的闭环控制：将 `group_wid` 纳入路由态，建立窗口漂移检测与自动回正能力。

## 本轮目标

1. ActionView 路由态新增 `group_wid`
2. grouped 窗口翻页/筛选重置路径统一清理 `group_wid`
3. grouped 加载流程新增 `group_wid` 与响应 `window_id` 的失配回正逻辑
4. runtime guard 增加 `group_wid` 关键标记约束
5. 完成回归与提交

## 验收口径

1. grouped 非首窗口在 `group_wid` 失配时会自动回正到首窗口并重新加载
2. 路由同步时可稳定写回 `group_wid`
3. grouped runtime guard 可检测该能力未被误删
4. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `make verify.contract.preflight`
