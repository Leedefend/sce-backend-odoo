# Odoo 原生承载差距迭代进展（v3.12-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 已完成

1. 后端 grouped 契约增强：
   - `group_paging.window_id` 回传当前窗口身份
   - `group_paging.query_fingerprint` 回传归一化查询指纹
   - meta 回传 `group_window_id/group_query_fingerprint`
2. 前端契约同步：
   - schema 增加 `ApiDataListResult.group_paging.window_id/query_fingerprint`
3. 消费侧同步：
   - ActionView 读取并记录 `window_id/query_fingerprint`
4. 文档同步：
   - grouped pagination contract 增补 `window_id/query_fingerprint`

## 验证结果

1. `make verify.grouped.governance.bundle`：PASS
2. `make verify.frontend.quick.gate`：PASS
3. `make verify.contract.preflight`：PASS

## 结论

grouped 分页契约已具备“窗口身份 + 查询指纹”语义，后续可据此进一步做窗口过期判定与跨端一致性保护。
