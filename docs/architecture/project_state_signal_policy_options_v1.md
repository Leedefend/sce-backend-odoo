# 项目状态 signal policy 方案对比 v1

状态：Governance Options  
批次：ITER-2026-04-13-1831

## 1. 对比目标

本文件只比较 `stage_id` 中 signal-based sync 与 standalone write 的治理方案，不修改代码。

基础约束：

- `lifecycle_state` 是项目真实状态；
- `stage_id` 是 Odoo UI 阶段投影；
- 目标同步方向为 `lifecycle_state -> stage_id`；
- `stage_id -> lifecycle_state` 禁止。

## 2. 方案 A：保留 signal-based stage sync，且保留 standalone stage write

定义：

- 保留 `_sync_stage_from_signals` 对 `stage_id` 的推进；
- 继续允许 standalone `stage_id` write 在防越级规则内生效；
- 不要求 `stage_id` 始终等于 `lifecycle_state` 映射结果。

| 维度 | 评估 |
| --- | --- |
| 优点 | 实现成本最低；保留当前已有交互；不需要立即调整用户拖动 stage 或信号同步路径。 |
| 风险 | `stage_id` 会同时承载 UI 阶段和业务信号进度，用户容易把 stage 当真实状态；迁移导入的生命周期真相与页面阶段可能不一致；后续排错成本高。 |
| 对迁移扩样的影响 | 不建议扩样。扩样后同一批项目可能因业务信号被推到不同 stage，而 `lifecycle_state` 仍停留在原状态。 |
| 对用户认知的影响 | 高风险。页面 stage 看起来像业务状态，但并非真实状态。 |
| 对后续实现工作量的影响 | 短期最小，长期最大。后续需要处理数据纠偏、用户认知纠偏和状态解释冲突。 |

结论：不推荐。

## 3. 方案 B：保留 signal-based stage sync，但限制 standalone stage write

定义：

- 禁止或严格限制用户/外部代码 standalone 写 `stage_id`；
- 仍保留 `_sync_stage_from_signals` 根据业务信号推进 `stage_id`；
- `stage_id` 继续不是纯 `lifecycle_state` 投影，而是 lifecycle + signal 的混合 UI 投影。

| 维度 | 评估 |
| --- | --- |
| 优点 | 消除人工拖动 stage 造成的部分漂移；保留业务信号自动推进的现有体验；实现工作量中等。 |
| 风险 | 核心问题仍存在：`stage_id` 仍可能脱离 `lifecycle_state`；信号推进不改变真实状态，会形成“页面阶段看似推进、业务真相未推进”的双层语义。 |
| 对迁移扩样的影响 | 仍不建议在当前 create-only 扩样中采用。除非明确把 stage 标注为“进度提示”而非状态，否则迁移语义仍不稳定。 |
| 对用户认知的影响 | 中高风险。用户不再能随意拖动 stage，但仍可能把信号推进后的 stage 误解为真实生命周期。 |
| 对后续实现工作量的影响 | 中等。需要限制 standalone stage 写入，同时仍要维护 signal sync 与生命周期状态之间的解释边界。 |

结论：只适合作为短期兼容方案，不适合作为目标态。

## 4. 方案 C：取消 signal-based stage sync，并收紧为 lifecycle 纯投影

定义：

- `stage_id` 只由 `lifecycle_state` 映射生成；
- 取消、禁用或重作用 `_sync_stage_from_signals` 对 `stage_id` 的直接写入；
- 禁止 standalone `stage_id` write 成为业务状态入口；
- 业务信号只可作为 advisory、指标、待办或后续生命周期变更建议，不直接改变 UI stage。

| 维度 | 评估 |
| --- | --- |
| 优点 | 语义最清晰；状态真相唯一；迁移数据可解释；用户看到的 stage 与生命周期一致；后续导入、回滚、扩样门禁更稳定。 |
| 风险 | 需要一次实现收口；现有依赖 signal 推进 stage 的体验会变化；需要补验证，避免误伤生命周期到 stage 的正常投影。 |
| 对迁移扩样的影响 | 最适合扩样。完成实现收口并验证通过后，可恢复 bounded create-only 扩样。 |
| 对用户认知的影响 | 最低风险。用户只需要理解 `lifecycle_state` 是真相，stage 是其 UI 表现。 |
| 对后续实现工作量的影响 | 短期中等，长期最低。一次性处理写入口和 signal sync，后续迁移与状态治理成本下降。 |

结论：推荐。

## 5. 方案对比结论

| 方案 | 是否作为目标态 | 是否允许当前扩样 | 总体判断 |
| --- | --- | --- | --- |
| A | 否 | 否 | 保留混乱，阻断扩样 |
| B | 否 | 否 | 可短期兼容，但仍未收口 |
| C | 是 | 当前否；实现收口 PASS 后可重新准入 | 推荐 |

