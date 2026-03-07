# Odoo 原生承载差距迭代计划（v3.6-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 目标定位

继续契约本体增强（非治理）。本轮聚焦 grouped 分组窗口的可继续性信号：后端明确告知当前窗口后是否还有更多分组。

## 本轮目标

1. 响应契约 `group_paging` 新增 `has_more`
2. `meta` 新增 `group_has_more`
3. 后端通过 `group_limit + 1` 探测得到稳定 `has_more`
4. 前端 schema 同步 `group_paging.has_more`
5. 文档补齐 `has_more` 语义

## 验收口径

1. `has_more=true` 时表示当前 `group_offset/group_limit` 窗口后仍有分组可拉取
2. `has_more=false` 时表示已到分组窗口尾部
3. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `make verify.contract.preflight`
