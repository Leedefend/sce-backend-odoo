# 交付冲刺 Blocker 清单 v1

## 结论（先说结论）
- 当前仓库已具备交付骨架与治理框架，但仍未达到“可放心客户试点”状态。
- 本轮冲刺目标是从“功能完备”切换为“交付封板”，优先清零 P0 Blocker。

## P0 Blocker（必须先清）
| ID | Blocker | 现状 | 验收标准 | Owner |
|---|---|---|---|---|
| B1 | 前端交付主链质量未封板 | `frontend gate` 未稳定全绿（ActionView/AppShell 主链存在 lint/typecheck 风险） | `pnpm -C frontend gate` 连续通过，主链文件无新增红线 | FE |
| B2 | Scene Contract / Provider shape 未完全封口 | 契约与 provider 边界仍存在“最小可跑”路径 | 交付包关键 scene 全部通过 contract/provider guard | BE |
| B3 | Capability gap backlog 失真 | 报告“全绿”但 gap backlog 缺少有效条目 | 建立真实 gap 分级（Blocker/Pilot Risk/Post-GA）并纳入发布门禁 | PM+Tech Lead |
| B4 | 交付证据不可一页审计 | 缺少“9模块×4角色旅程”可追溯证据板 | 输出一页 readiness scoreboard（commit/db/seed/结果） | Delivery |
| B5 | 财务跨角色审批交接阻塞 | `verify.portal.payment_request_approval_all_smoke.container` 失败，`executive` 在提交后无可执行 follow-up 动作 | `payment_request_approval_all_smoke` 全链路通过（submit→handoff→approve/reject） | Finance+BE |

## P1（紧随其后）
- 关键角色旅程脚本化（PM/财务/采购/老板）。
- 搜索/筛选/分页/批量动作的交付状态显式化。

## 冲刺边界
- 冻结新增 capability；仅处理 Blocker 和交付闭环。
- 变更优先级：稳定性 > 新功能。
