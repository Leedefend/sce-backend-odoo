# 项目状态 signal policy 推荐结论 v1

状态：Governance Recommendation  
批次：ITER-2026-04-13-1831

## 1. 推荐方案

推荐采用：方案 C，取消 signal-based stage sync，并收紧为 lifecycle 纯投影。

目标规则：

```text
lifecycle_state = business truth
stage_id = lifecycle_state 的 Odoo UI projection
lifecycle_state -> stage_id
stage_id -/-> lifecycle_state
business signals -/-> stage_id
standalone stage_id write -/-> business state
```

## 2. 推荐理由

1. 状态真相必须唯一  
   1829 已冻结 `lifecycle_state` 为业务真相。若保留 signal-based `stage_id` 推进，`stage_id` 会继续表达另一套业务事实，破坏真相层唯一性。

2. 迁移扩样需要可解释状态  
   create-only 项目骨架导入只应写安全字段。若 stage 可被业务信号或人工写入独立改变，扩样后页面状态与导入状态之间会出现解释成本。

3. 用户认知需要收敛  
   Odoo 原生 stage 在页面上具有强状态暗示。若它不是纯投影，用户会自然把 stage 当作真实项目状态，导致“状态错乱”。

4. 后续实现成本更可控  
   方案 C 短期需要实现收口，但长期减少双状态解释、迁移门禁、回滚核验和页面认知的反复修正。

## 3. 当前是否允许 bounded create-only 扩样

不允许。

当前实现状态下，bounded create-only 扩样仍被阻断，原因是：

- `_sync_stage_from_signals` 仍可能不经 `lifecycle_state` 推进 `stage_id`；
- standalone `stage_id` write 仍存在；
- `stage_id` 当前不是纯 lifecycle 投影。

## 4. 扩样前必须完成的实现收口动作

进入扩样前，必须先开实现收口批次并完成以下动作：

| 动作 | 目标 |
| --- | --- |
| 收紧 standalone `stage_id` write | `stage_id` 不再作为独立业务状态入口 |
| 处理 `_sync_stage_from_signals` | 不再独立写 `stage_id`；必要时改为 advisory 或后续建议，不改变 UI stage |
| 保留 lifecycle -> stage 映射 | `create()` / `write(lifecycle_state)` / lifecycle sync 仍能正确设置 `stage_id` |
| 保留 stage seed | `project.stage` 继续作为 Odoo UI 投影字典存在 |
| 增加验证 | 证明 lifecycle 改变会投影 stage，signal 不会独立推进 stage，stage 不会反写 lifecycle |

## 5. 推荐准入结论

| 项 | 结论 |
| --- | --- |
| 推荐方案 | C |
| 是否接受 signal-based stage sync | 不接受作为目标态 |
| 是否接受 standalone stage write | 不接受作为目标态 |
| 当前是否允许扩样 | 不允许 |
| 下一步 | 开“项目状态纯投影实现收口专项” |

