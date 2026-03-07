# Odoo 原生承载差距迭代进展（v3.22-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 已完成

1. 后端兼容增强：
   - `group_paging` 新增平铺字段 `window_key`
   - `meta` 同步新增 `group_window_key`
2. 前端消费增强：
   - ActionView 读取 `window_identity.key`，缺失时回退 `window_key`
3. 类型与文档同步：
   - schema 新增 `group_paging.window_key`
   - grouped contract 文档补充 `window_key` 兼容说明
4. 校验增强：
   - grouped smoke 新增 `identity_key_matches_flat` 校验
   - semantic/consistency/runtime guards 同步新增 `window_key` 相关约束

## 验证结果

1. `make verify.grouped.governance.bundle`：PASS
2. `make verify.frontend.quick.gate`：PASS
3. `make verify.contract.preflight`：PASS

## 结论

grouped 窗口身份契约具备 object+flat 双通道兼容能力，客户端演进可更平滑。
