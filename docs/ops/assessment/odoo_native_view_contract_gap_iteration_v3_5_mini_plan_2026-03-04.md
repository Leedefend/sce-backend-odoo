# Odoo 原生承载差距迭代计划（v3.5-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v3_4`

## 目标定位

继续契约本体增强（非治理）。本轮聚焦 grouped 分组结果自身的分页偏移契约：允许客户端请求分组窗口偏移，后端回传生效偏移。

## 本轮目标

1. 请求契约新增 `group_offset`
2. 响应契约 `group_paging` 新增 `group_offset`
3. meta 回传 `group_offset`
4. 前端 schema 与调用透传同步
5. 文档补齐 `group_offset` 约定

## 验收口径

1. 分组条目可通过 `group_offset + group_limit` 做窗口化获取
2. 后端回传生效偏移，客户端无需猜测
3. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`
