# 交付冲刺 Blocker 清单 v1

## 结论（先说结论）
- 当前仓库交付骨架、治理框架与 9 模块 system-bound 证据已完成最终收口。
- 本轮 P0 Blocker 已清零，后续优化进入常规迭代。
- 最终收口日期：`2026-07-05`

## P0 Blocker（最终状态）
| ID | Blocker | 现状 | 验收标准 | Owner | 状态 |
|---|---|---|---|---|---|
| B1 | 前端交付主链质量未封板 | `verify.frontend.typecheck.strict` 与 `verify.frontend.build` 通过 | 前端主链无新增红线 | FE | CLOSED |
| B2 | Scene Contract / Provider shape 未完全封口 | `verify.scene.delivery.readiness.role_matrix` 通过 | 交付包关键 scene 通过 contract/provider guard | BE | CLOSED |
| B3 | Capability gap backlog 失真 | scene/product delivery readiness 已纳入 role matrix 证据链 | gap 分级与发布门禁证据可追溯 | PM+Tech Lead | CLOSED |
| B4 | 交付证据不可一页审计 | readiness scoreboard 与 9 模块矩阵已更新为 PASS | 输出一页 readiness scoreboard（commit/db/seed/结果） | Delivery | CLOSED |
| B5 | 财务跨角色审批 handoff | `verify.portal.payment_request_approval_all_smoke.container` 通过，executive 可执行 `approve/reject` handoff | `payment_request_approval_all_smoke` 全链路通过（submit→handoff→approve/reject） | Finance+BE | CLOSED |

## P1（紧随其后）
- 关键角色旅程扩展覆盖率继续进入常规迭代。
- 搜索/筛选/分页/批量动作的细粒度体验优化继续进入 P2。

## 冲刺边界
- 冻结新增 capability；仅处理 Blocker 和交付闭环。
- 变更优先级：稳定性 > 新功能。
- 固化门禁：`make verify.release.delivery_9_module.final_closeout.guard`
- 核心证据：`verify.scene.delivery.readiness.role_matrix`、`verify.portal.payment_request_approval_all_smoke.container`、`verify.portal.payment_request_approval_field_consumer_audit`
