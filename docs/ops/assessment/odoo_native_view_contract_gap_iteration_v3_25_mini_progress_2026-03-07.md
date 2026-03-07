# Odoo 原生承载差距迭代进展（v3.25-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 已完成

1. 契约增强：
   - `window_identity` 新增 `prev_group_offset/next_group_offset/has_more`
   - `meta.group_window_identity` 同步输出导航字段
2. 类型增强：
   - schema 同步新增 identity 导航字段
3. 校验增强：
   - grouped smoke 新增 identity 导航字段存在性与 flat 对齐校验
   - semantic/consistency/runtime guards 同步新增约束
4. 文档同步：
   - grouped contract 补齐 `window_identity` 导航字段定义

## 验证结果

1. `make verify.grouped.governance.bundle`：PASS
2. `make verify.frontend.quick.gate`：PASS
3. `make verify.contract.preflight`：PASS

## 结论

`window_identity` 已具备窗口导航语义的内聚表达，进一步减少对外层字段组合解析的依赖。
