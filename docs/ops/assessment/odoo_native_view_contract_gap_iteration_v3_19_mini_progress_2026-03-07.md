# Odoo 原生承载差距迭代进展（v3.19-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 已完成

1. 后端契约形态增强：
   - `group_paging` 新增 `window_identity` 对象
   - `meta` 同步新增 `group_window_identity`
2. 前端消费增强：
   - ActionView 在 grouped 加载时优先读取 `window_identity`
   - 对平铺字段 `window_id/query_fingerprint/window_digest` 保持兼容回退
3. 校验增强：
   - grouped smoke 新增 identity object 存在性与平铺字段一致性检查
   - semantic/consistency/runtime guards 同步新增标记约束
4. 文档同步：
   - schema 与 grouped contract 增加 `window_identity` 定义与兼容规则

## 验证结果

1. `make verify.grouped.governance.bundle`：PASS
2. `make verify.frontend.quick.gate`：PASS
3. `make verify.contract.preflight`：PASS

## 结论

grouped 窗口身份已形成标准化对象表达，契约形态更稳健，前后端演进时可降低字段分散引发的不一致风险。
