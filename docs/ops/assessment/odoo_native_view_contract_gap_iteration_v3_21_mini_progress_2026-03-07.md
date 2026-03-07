# Odoo 原生承载差距迭代进展（v3.21-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 已完成

1. 后端契约增强：
   - `window_identity` 新增统一身份键 `key`
   - `meta.group_window_identity` 同步输出 `key`
2. 前端路由闭环增强：
   - ActionView 新增 `groupWindowIdentityKey`
   - 路由新增 `group_wik` 读写同步与 HUD 观测
   - grouped 非首窗口下 `group_wik` 失配自动回正
3. 校验链路增强：
   - grouped smoke 新增 `window_identity.key` 存在性与 tuple 匹配校验
   - semantic/consistency/runtime guards 同步新增约束
4. 文档同步：
   - grouped contract 新增 `group_wik` 路由键与 `window_identity.key` 说明

## 验证结果

1. `make verify.grouped.governance.bundle`：PASS
2. `make verify.frontend.quick.gate`：PASS
3. `make verify.contract.preflight`：PASS

## 结论

grouped 窗口身份已具备“多字段+单键”双形态表达，前端可用单键完成快速漂移检测，同时保持细粒度字段兼容。
