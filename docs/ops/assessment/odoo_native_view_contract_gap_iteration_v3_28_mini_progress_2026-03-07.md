# Odoo 原生承载差距迭代进展（v3.28-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 已完成

1. 契约增强：
   - `window_identity` 新增 `group_by_field`
   - `meta.group_window_identity` 同步携带分组维度
2. 类型增强：
   - schema 新增 `window_identity.group_by_field`
3. 校验增强：
   - grouped smoke 新增 `group_by_field` 对齐校验
   - semantic/consistency/runtime guards 同步新增约束
4. 文档同步：
   - grouped contract 补齐 `window_identity.group_by_field` 定义

## 验证结果

1. `make verify.grouped.governance.bundle`：PASS
2. `make verify.frontend.quick.gate`：PASS
3. `make verify.contract.preflight`：PASS

## 结论

`window_identity` 已具备分组维度自描述能力，identity 在跨层消费时的上下文完整性进一步提升。
