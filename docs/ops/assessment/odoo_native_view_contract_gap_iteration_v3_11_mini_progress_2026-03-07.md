# Odoo 原生承载差距迭代进展（v3.11-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 已完成

1. 后端 grouped 契约增强：
   - `group_paging.window_start/window_end` 回传当前分组窗口范围
   - meta 回传 `group_window_start/group_window_end`
2. 前端契约同步：
   - schema 增加 `ApiDataListResult.group_paging.window_start/window_end`
3. 消费侧落地：
   - ActionView 解析并存储后端窗口范围
   - GroupSummaryBar 优先展示后端窗口范围，缺省时回退本地推导
4. 契约文档同步：
   - grouped pagination contract 增补 `window_start/window_end`

## 验证结果

1. `make verify.grouped.governance.bundle`：PASS
2. `make verify.frontend.quick.gate`：PASS
3. `make verify.contract.preflight`：PASS

## 结论

grouped 分组窗口契约由“偏移 + 数量推导”升级为“后端直接回传窗口范围”，前端展示与路由回放一致性进一步增强。
