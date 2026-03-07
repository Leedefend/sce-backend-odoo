# Odoo 原生承载差距迭代进展（v3.23-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 已完成

1. 契约增强：
   - `window_identity` 新增 `group_offset/group_limit/group_count`
   - `meta.group_window_identity` 同步输出上述字段
2. 类型增强：
   - schema 同步新增 identity 数字字段
3. 校验增强：
   - grouped smoke 新增 identity 数字字段存在性与 flat 对齐校验
   - semantic/consistency/runtime guards 同步新增约束
4. 文档同步：
   - grouped contract 补齐 `window_identity` 数字字段定义

## 验证结果

1. `make verify.grouped.governance.bundle`：PASS
2. `make verify.frontend.quick.gate`：PASS
3. `make verify.contract.preflight`：PASS

## 结论

`window_identity` 已升级为完整自描述对象，跨层消费时对外层 `group_paging` 字段依赖降低。
