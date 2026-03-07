# Odoo 原生承载差距迭代计划（v3.10-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 目标定位

继续契约本体增强（非治理）。本轮聚焦 grouped `group_offset` 深链回放验证：将 offset 回放语义固化进 smoke 签名与语义 guard。

## 本轮目标

1. `fe_tree_view_smoke` 新增 `group_offset` 回放请求
2. 导出 `grouped_offset_replay_summary`（request/response/consistency）
3. semantic/drift/consistency guard 增加新摘要字段约束
4. grouped signature baseline 同步更新
5. 文档记录本轮验证能力增强

## 验收口径

1. smoke 可验证 `response.group_paging.group_offset == request.group_offset`
2. `next_group_offset/prev_group_offset` 类型与语义在 baseline 中可审计
3. 回归通过：
   - `make verify.grouped.governance.bundle`
   - `make verify.frontend.quick.gate`
   - `make verify.contract.preflight`
