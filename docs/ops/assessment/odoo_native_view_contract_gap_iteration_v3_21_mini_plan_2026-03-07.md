# Odoo 原生承载差距迭代计划（v3.21-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 目标定位

继续契约本体增强（非治理）。本轮聚焦 grouped 窗口身份单键化：在 `window_identity` 增加统一键 `key`，并在前端路由引入 `group_wik` 作为单键防漂移锚点。

## 本轮目标

1. 后端 `window_identity` 增加 `key`
2. 前端 ActionView 新增 `groupWindowIdentityKey` 与路由键 `group_wik`
3. grouped 加载流程新增 `group_wik` 失配回正逻辑
4. smoke/guard 增加 identity key 形状与一致性校验
5. 完成回归与提交

## 验收口径

1. grouped 响应包含 `group_paging.window_identity.key`
2. HUD 可观测 `group_window_identity_key` 与 `route_group_wik`
3. 非首窗口下 `group_wik` 失配时自动回正并重载
4. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `make verify.contract.preflight`
