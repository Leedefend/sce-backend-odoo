# Contract Alignment Acceptance v1

## Scope
- 对象范围：`project.project` / `project.task` / `project.budget` / `project.cost.ledger` / `payment.request` / `sc.settlement.order`
- 验收目标：补齐“业务事实层 ↔ 契约层 ↔ 前端消费层”中间证据并形成冻结基线。
- 约束：不新增业务逻辑、不改后端业务事实、不做前端权限补丁。

## Batch A 结论（对象盘点）
- 已完成六对象 `list/form/rights/runtime` 契约面盘点。
- 已形成稳定字段/差异字段/前端真实依赖字段矩阵。
- 证据：`docs/ops/contract_alignment_object_inventory_v1.md:1`

## Batch B 结论（contract-native 一致性）
- 六对象在 `create/edit/readonly/restricted/deny-path` 语义上与原生办理结果同向一致。
- 原生最小办理与 outsider deny 证据链可追溯。
- 证据：
  - `docs/ops/contract_alignment_native_consistency_v1.md:1`
  - `agent_ops/reports/2026-04-07/report.ITER-2026-04-07-1296.md:25`
  - `agent_ops/reports/2026-04-07/report.ITER-2026-04-07-1297.md:7`

## Batch C 结论（contract-frontend 消费一致性）
- 六对象前端真实消费字段集合与当前 contract 面一致，未发现对象级消费偏移。
- 识别到通用兜底掩盖风险（rights/view_type fallback），已纳入冻结面控制。
- 证据：`docs/ops/contract_consumer_dependency_v1.md:1`

## Final verdict
- 本阶段结论：`PASS`
- 当前可确认：
  - 契约表达与原生事实一致。
  - 前端消费与契约表达一致。
  - 现阶段最小契约面可冻结并进入变更门禁管理。

## Controlled follow-up
- 后续任何涉及冻结字段的调整，必须先更新 `docs/ops/contract_freeze_surface_v1.md` 并附变更影响评估。
- 未完成冻结面审查前，不允许直接在实现层引入“前端兜底”式补丁来掩盖 contract 漏字段。
