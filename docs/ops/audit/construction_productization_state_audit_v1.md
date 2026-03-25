# Construction Productization State Audit v1

## 1. 审计范围

本次审计只做读侧核查，不修改代码、不新增模块、不重构。

审计对象：

- released scenes
- 主线 scene chain
- next_actions runtime
- project state write paths
- dashboard / workspace 聚合能力
- 用户主路径断点

证据产物：

- `artifacts/audit/scene_registry_dump.json`
- `artifacts/audit/released_scenes.json`
- `artifacts/audit/scene_flow_map.json`
- `artifacts/audit/scene_openability.json`
- `artifacts/audit/next_actions_sources.json`
- `artifacts/audit/next_actions_runtime.json`
- `artifacts/audit/next_actions_consistency.json`
- `artifacts/audit/state_transition_map.json`
- `artifacts/audit/dashboard_candidates.json`
- `artifacts/audit/user_flow_breakpoints.json`

## 2. Scene 能力表

| scene | openable | next_actions | state_write | usable |
| --- | --- | --- | --- | --- |
| `projects.intake` | 是 | 无显式 released next_actions，靠入口动作卡片 | 新建项目，不承担主阶段推进 | 是 |
| `project.management` | 是 | 有，能桥接 `project.plan_bootstrap` / `project.execution` | 部分，主要通过内部执行链驱动 | 部分可用 |
| `cost` | 是 | 有，运行时可达 `payment.enter` / `settlement.enter` | 否，写成本记录，不写项目主阶段 | 是 |
| `payment` | 是 | 有，运行时可达 `settlement.enter` | 否，写付款记录，不写项目主阶段 | 是 |
| `settlement` | 是 | 无 | 否，当前只读汇总 | 是 |
| `my_work.workspace` | 是 | 不属于主线推进型 next_actions | 否 | 是 |

## 3. 主线完整性

目标主线：

`projects.intake -> project.plan_bootstrap -> project.execution -> cost.tracking -> payment -> settlement`

审计结论：

**是否可形成闭环：NO**

原因不是主线不存在，而是 released product surface 与内部 carrier 之间仍有一层未完全收口的项目上下文连接层：

- internal chain 存在
- released routes 存在
- execution / cost / payment / settlement runtime 也能互相跳转
- 但 FR-2 到 FR-5 的 released route 仍依赖 `release entry shell + project context handoff`

因此，当前状态更准确地说是：

- **内部能力链已成立**
- **released product chain 仍未完全自闭合**

## 4. next_actions 状态

结论：

**部分统一**

证据：

- `project.execution` runtime next_actions 已具备统一 action 列表，并包含：
  - `project.execution.advance`
  - `cost.tracking.enter`
  - `payment.enter`
  - `settlement.enter`
- `cost` runtime next_actions 已包含：
  - `cost.tracking.block.fetch`
  - `payment.enter`
  - `settlement.enter`
- `payment` runtime next_actions 已包含：
  - `payment.block.fetch`
  - `settlement.enter`
- `settlement` runtime next_actions 为空

结构性问题：

- `kind / action_kind` 在实际 runtime 中未统一落出，当前为空
- next_actions 有统一 `intent`，但“guidance / transition”语义尚未成为稳定协议

## 5. 用户可用性结论

**B. 需补连接层**

当前系统已经不是“零散功能”，而是具备了明显的产品雏形：

- released scenes 已形成
- 主线 carrier 已存在
- execution 到 cost/payment/settlement 的跳转真实可达
- 读写协议、审批、审计、发布面治理都已成型

但要称为“可交付产品”，还差一层关键收口：

- released product route
- project context
- internal scene carrier
- next_actions contract

这四者还没有收成一个统一的产品连接层。

## 6. 关键发现

### 6.1 Released surface 已存在

`released_scenes.json` 显示当前已发布 scene 为：

- `projects.intake`
- `project.management`
- `cost`
- `payment`
- `settlement`
- `my_work.workspace`

### 6.2 主线 carrier 已存在

`scene_flow_map.json` 与 verify 脚本共同证明内部 carrier 主线存在：

- `project.plan_bootstrap.enter`
- `project.execution.enter`
- `cost.tracking.enter`
- `payment.enter`
- `settlement.enter`

### 6.3 execution 是当前主线神经中枢

`next_actions_runtime.json` 表明：

- `project.execution` 是当前主线里最完整的调度节点
- `cost / payment / settlement` 都由它向外辐射

### 6.4 state write 仍不是产品化行为推进模型

`state_transition_map.json` 表明：

- `project.execution.advance` 写的是 `project.task.state`
- `cost.tracking.record.create` 与 `payment.record.create` 只写业务记录
- `project.stage_id` 的变化主要仍来自：
  - `lifecycle_state -> stage_id`
  - `_sync_stage_from_signals()`

这意味着当前主阶段推进仍偏“信号/派生”，不是“显式产品动作推进”。

### 6.5 Dashboard 能力存在，但仍偏承载层

`dashboard_candidates.json` 证明：

- `project.dashboard`
- `workspace_home`
- summary/fact blocks

这些聚合能力已存在，但更像承载和汇总层，不是已经收口完成的“产品驾驶舱规范”。

## 7. TOP 5 缺口

1. FR-2 到 FR-5 的 released route 仍依赖 `release entry shell` 传递 `project_id`，released surface 还未完全自闭合。
2. next_actions 虽然可运行，但 `guidance / transition` 语义没有在 runtime contract 中稳定落出。
3. `settlement` 作为终点场景是只读汇总，没有“终局动作”或完成态引导，主线尾端仍偏薄。
4. `project.stage` 的推进真源仍偏 `lifecycle/signal sync`，而不是显式产品动作驱动。
5. `project.management` 同时承担 released product entry、dashboard、plan/execution bridge，产品语义与 carrier 语义仍然混合。

## 8. 审计结论

当前系统已经具备“拼成一个产品”的大部分条件，但还不能判定为 fully productized release surface。

更准确的判定是：

- **内部产品链：成立**
- **released 产品面：接近成立**
- **正式可交付产品：还差一层连接层收口**

## 9. 唯一建议方向

**下一轮只做一件事：补“released scene 连接层”**

定义：

- 统一 FR-2 到 FR-5 的 released route 进入协议
- 把 `release entry shell + recent project / project picker / project_id handoff`
  收口成正式 contract
- 同时把 next_actions 的 `guidance / transition` 语义补成稳定 runtime 字段

目标不是再做新功能，而是把：

`released route -> project context -> internal carrier -> next_actions`

收成一个真正可交付的产品连接层。
