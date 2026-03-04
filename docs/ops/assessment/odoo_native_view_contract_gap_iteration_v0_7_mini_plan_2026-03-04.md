# Odoo 原生承载差距迭代计划（v0.7-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v0_7`

## 目标来源（评估报告映射）

延续“治理驱动契约能力增强”的方向，在已有 grouped 分页语义基础上，进一步增强契约可表达性与前端消费一致性，减少前后端重复推导。

## 本轮目标（执行项）

1. 后端 grouped 契约补充 `page_has_prev/page_has_next` 语义字段
2. 前端 grouped 翻页按钮优先消费后端 `page_has_prev/page_has_next`
3. 后端 grouped 契约补充 `group_key` 明确标识（统一 key 语义）
4. 前端 `ActionView` 优先消费后端 `group_key`（兼容旧构造）
5. tree smoke 增加 grouped page flags 与 group_key 覆盖断言
6. grouped 语义 baseline 更新并保持 drift guard 通过
7. grouped runtime guard 增加新字段链路标记
8. contract evidence 导出补充 grouped pagination 能力摘要
9. 更新 v0.7-mini 进展文档
10. 完成本轮统一回归（quick gate + tree smoke + preflight fast）

## 提交节奏（约 10 个独立提交）

1. docs: v0.7-mini 计划
2. feat(contract): grouped rows 增加 page_has_prev/page_has_next
3. feat(frontend): ListPage 翻页按钮消费 page flags
4. feat(contract): grouped rows 增加 group_key
5. feat(frontend): ActionView 优先消费后端 group_key
6. test(smoke): grouped page flags/group_key 断言
7. test(guard): grouped_rows_runtime_guard 新标记
8. feat(evidence): contract evidence grouped pagination 能力摘要
9. docs: v0.7-mini 进展
10. chore(verify): round gate 回归收口

## 验收口径

1. grouped 响应具备 `group_key/page_has_prev/page_has_next` 且前端可直接消费
2. tree smoke 对新字段有断言且 baseline 不漂移
3. grouped runtime guard 覆盖新增链路
4. 以下命令通过：
   - `make verify.frontend.quick.gate`
   - `make verify.portal.tree_view_smoke.container`
   - `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`
