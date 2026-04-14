# 项目状态实现收口决策 v1

状态：Governance Decision  
批次：ITER-2026-04-13-1831  
依据：ITER-2026-04-13-1829 状态治理决策；ITER-2026-04-13-1830 实现对齐审计

## 1. 已冻结前提

本轮不重新定义状态体系，只对实现收口方向作决策。

已冻结规则：

| 项 | 决策 |
| --- | --- |
| 真实状态 | `lifecycle_state` |
| UI 阶段投影 | `stage_id` |
| 同步方向 | `lifecycle_state -> stage_id` |
| 禁止方向 | `stage_id -/-> lifecycle_state` |
| 导入策略 | 导入写 `lifecycle_state`，再映射 `stage_id` |

## 2. 当前实现事实

ITER-2026-04-13-1830 确认：

| 项 | 结论 |
| --- | --- |
| lifecycle -> stage 路径 | 存在 |
| stage -> lifecycle 反写 | 未发现直接路径 |
| standalone `stage_id` write | 存在，可在防越级范围内单独改变 UI stage |
| signal-based stage sync | 存在，`_sync_stage_from_signals` 可基于 BOQ/task/material/settlement/payment 信号推进 `stage_id`，但不改变 `lifecycle_state` |
| 当前 stage 性质 | 不是纯 lifecycle 投影，而是 `UI stage + 业务信号投影` |

## 3. 收口决策

| 问题 | 决策 |
| --- | --- |
| 是否接受 signal-based stage sync 继续存在 | 不接受作为目标态。可作为历史过渡行为被识别，但必须在实现收口批次中移除、禁用或改造成不写 `stage_id` 的 advisory 逻辑。 |
| 是否接受 standalone `stage_id` write 继续存在 | 不接受作为目标态。`stage_id` 不能作为独立业务状态写入口。 |
| 最终目标是否仍是 stage 纯投影 | 是。目标态仍是 `stage_id = lifecycle_state 的 UI 投影`。 |
| 当前系统是过渡态还是目标态 | 过渡态。当前实现不满足纯投影目标。 |

## 4. 当前准入结论

当前不允许扩大 create-only 项目骨架样本。

原因：

- signal-based stage sync 会让 `stage_id` 表达业务信号推进，而不是只表达生命周期真相；
- standalone `stage_id` write 会让用户或代码在不改变 `lifecycle_state` 的情况下改变 UI stage；
- 扩样后用户可能把 stage 当成真实状态理解，造成迁移数据语义混乱。

允许继续保留的短期前提：

- 已写入 30 条试导记录不需要立即回滚；
- 继续只读复核、真实回滚 dry-run、状态实现收口设计是允许的；
- 在实现收口完成前，不进入下一批 create-only 扩样。

## 5. 目标态定义

目标态必须满足：

| 行为 | 目标态规则 |
| --- | --- |
| `lifecycle_state` 写入 | 允许，按业务规则校验后同步投影到 `stage_id` |
| `stage_id` 写入 | 不作为业务状态入口；不得独立改变项目真实状态 |
| `_sync_stage_from_signals` | 不得独立写 `stage_id`；业务信号只能形成 advisory 或后续生命周期建议，不直接推进 UI stage |
| 导入 | 只写 `lifecycle_state` 与 legacy 对照字段，不独立写 `stage_id` |
| 用户拖动 stage | 不允许反向修改 `lifecycle_state`；目标态下也不应形成独立 UI 阶段事实 |

## 6. 决策状态

本轮结论为：选择收紧方向，当前系统为过渡态，扩样继续阻断。

