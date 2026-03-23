# Phase 2 Batch-B ActionView State Host Boundary

## 批次信息

- 批次：Batch-B
- 前置条件：
  - Batch-A 已完成并收口，见 [phase_2_a_actionview_runtime_split_boundary.md](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/docs/ops/releases/current/phase_2_a_actionview_runtime_split_boundary.md)
- 唯一目标：
  - 继续压缩 `ActionView` 页面 state host，让 assembler/runtime 接管更多 display/state glue
- 成功口径：
  - `ActionView.vue` 从“模板消费 + 局部状态 host + 路由桥接”继续推进到“模板消费 + 少量路由桥接”

## 范围

- 允许改动：
  - [ActionView.vue](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/views/ActionView.vue)
  - [useActionPageModel.ts](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/app/assemblers/action/useActionPageModel.ts)
  - `frontend/apps/web/src/app/assemblers/action/*`
  - `frontend/apps/web/src/app/action_runtime/*`
  - 与 `ActionView` 直接耦合的最小 verify/doc
- 禁止改动：
  - 不改后端 contract
  - 不新增业务能力
  - 不同时拆 `RecordView` / `SceneView` / `HomeView`
  - 不做全局 router/shell 重构
  - 不把 Batch-B 扩成“整个前端 page assembly 重写”

## Batch-A 后的现状判断

- 已完成：
  - `load` dispatch 已从页面 mutable bridge 外移
  - `action` 副作用 facade 已独立
  - `batch` 副作用 facade 已独立
  - `advanced rows` 纯展示派生已进入 assembler
- 未完成：
  - 页面仍集中持有较大的状态面：
    - `status`
    - `traceId`
    - `records`
    - `selectedIds`
    - `batch*`
    - `group runtime state`
  - 页面仍保留较多 display/state glue：
    - hud 输入聚合
    - filter/group/summary 的中间态拼装
    - list/kanban/advanced 多模式的部分展示派生
  - assembler 仍不是唯一 VM 主入口

## 核心判断

- Batch-B 不再优先处理 `load/action/batch` 主链控制权。
- Batch-B 的主问题是：
  - 哪些状态应该继续留在页面
  - 哪些状态应该变成 runtime capsule
  - 哪些展示派生应该进入 assembler
- 因此 Batch-B 的切法必须围绕：
  - `state host`
  - `display glue`
  - `group runtime capsule`

## 实施步骤

### Step 1：State Host Recalibration

- 操作：
  - 重新盘点 `ActionView` 当前仍留在页面的状态面，按三类归档：
    - 必须留在页面的桥接状态
    - 可进入 runtime capsule 的交互状态
    - 可进入 assembler 的纯展示派生状态
- 输出：
  - Batch-B 状态热区清单
  - 页面保留态白名单

完成判据：
- 能明确指出每类状态的归宿
- 不再把“所有 ref 都要外移”当成目标

### Step 2：Display Glue Into Assembler

- 操作：
  - 继续把只服务模板渲染的展示派生从 `ActionView` 推进 `useActionPageModel`
  - 优先处理：
    - hud 条目输入的中间态
    - list/kanban/advanced 纯展示摘要
    - focus/empty/summary 的展示型拼装
- 输出：
  - assembler 输入面扩大
  - 页面本地 `computed` 数量下降

完成判据：
- 页面不再持有一批仅为 `vm.*` 服务的展示拼装
- `useActionPageModel` 更接近唯一 VM 装配入口

### Step 3：Interactive State Capsule

- 操作：
  - 把交互型但非模板桥接的状态面推进 runtime capsule
  - 优先候选：
    - `selectedIds`
    - `batch*`
    - 与 group window 相关的部分状态
- 输出：
  - `ActionView` 页面状态面显著收缩
  - runtime capsule 的职责更清晰

完成判据：
- 页面不再直接承载大块交互状态面
- 相关状态的更新路径可以从单一 capsule 追踪

### Step 4：Group Runtime Boundary Review

- 操作：
  - 评估 `group runtime state` 是否可以形成独立 capsule 或 assembler 输入边界
  - 只做最小闭环，不追求一次拆完全部 group 逻辑
- 输出：
  - group runtime 的明确归宿决定：
    - 保留在页面
    - 进入 runtime capsule
    - 进入 assembler 输入

完成判据：
- group runtime 不再是“默认留在页面的大包袱”
- 得到一个明确、可执行的归属结论

### Step 5：Page Shell Review

- 操作：
  - 在前四步完成后，重新判断 `ActionView` 是否已接近 page shell 形态
  - 补更新库存和阶段结论
- 输出：
  - Batch-B closure 结论
  - 下一批是否继续拆 `ActionView` 的判断

完成判据：
- 能清楚回答：
  - 页面还剩哪些状态
  - 为什么这些状态必须留
  - 下一批是否仍值得继续拆

## 页面保留态白名单

Batch-B 允许暂时保留在页面的状态，必须满足至少一条：

- 直接参与路由桥接
- 直接参与生命周期触发
- 无法在不扩大 contract 的前提下自然下沉
- 已经是某个 runtime/capsule 的装配入口，只剩一层薄桥接

不满足以上条件的状态，不应默认继续留在页面。

## 验证门禁

- 必跑：
  - `make verify.frontend.typecheck.strict`
  - `make verify.product.final_slice_readiness_audit`
- 按变更面补跑：
  - `make verify.frontend.zero_business_semantics`
  - 与 `ActionView` 相关的 list/view/render/execute button smoke
- 文档同步：
  - 如批次内状态归宿发生实质变化，更新：
    - [frontend_architecture_violation_inventory_v1.md](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/docs/architecture/frontend_architecture_violation_inventory_v1.md)
    - [actionview_runtime_hotspot_map_v1.md](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/docs/architecture/actionview_runtime_hotspot_map_v1.md)

## 停机条件

- `ActionView` 页面剩余状态无法按“桥接 / capsule / assembler”三类稳定归档
- 拆分后 `verify.frontend.typecheck.strict` 失败
- 拆分后 `final_slice_readiness_audit` 不再为绿
- 为了继续拆状态 host，不得不引入后端 contract 变更
- 发现 assembler 继续扩张会吞掉 runtime 职责，开始形成新的职责混乱

## 回滚原则

- 仍按 Step 颗粒度提交
- 每步失败只回滚当前 state/display 归宿相关模块
- 不跨 Step 混入额外页面治理任务

## 批次结论

- Batch-B 是 `ActionView` 的“state host 收缩批次”，不是新的 runtime 主链拆分批次
- 正确顺序应是：
  1. 先校准页面剩余状态归宿
  2. 再推进 display glue 进 assembler
  3. 再推进 interactive state 进 capsule
  4. 最后再判断 page shell 化程度
- 如果 Batch-B 结束后页面仍保留大量不可解释状态面，才考虑是否需要 Batch-C

---

## Batch-B 执行结果

- 状态：已完成
- 完成日期：2026-03-23
- 结果判断：
  - Batch-B 已完成“state host 收缩批次”的预定目标
  - `ActionView` 进一步从“页面承载大量交互与展示中间态”推进到“页面主要承载核心 load 数据面、group bridge、route/lifecycle bridge”
  - 当前已不适合继续在 Batch-B 内做零碎收缩，后续应进入下一批判断

### 本批提交

1. `f71c8d1` `Define ActionView Phase 2 Batch-B boundary`
2. `cd22ebd` `Shrink ActionView state host and HUD assembly`

### 已完成项

- Step 1：State Host Recalibration
  - 页面剩余状态已按三类重新归档：
    - 页面桥接保留态：`route/lifecycle/load host`
    - runtime capsule：`selection/batch/group`
    - assembler 展示派生：`advanced rows/hud entries`
- Step 2：Display Glue Into Assembler
  - HUD 条目拼装已进入 [useActionPageModel.ts](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/app/assemblers/action/useActionPageModel.ts)
  - `advanced rows` 已在上一批进入 assembler
- Step 3：Interactive State Capsule
  - 新增 [actionViewSelectionRuntimeState.ts](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/app/runtime/actionViewSelectionRuntimeState.ts)
  - 新增 [actionViewBatchRuntimeState.ts](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/app/runtime/actionViewBatchRuntimeState.ts)
  - [ActionView.vue](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/views/ActionView.vue) 不再逐个声明 selection/batch 基础 ref
- Step 4：Group Runtime Boundary Review
  - 结论：`group runtime state` 已有独立 capsule，当前问题不在“状态是否独立”，而在“page shell 仍承担 route/drilldown bridge”
  - 因此本批不继续拆 group 主逻辑，而将其纳入下一批重点
- Step 5：Page Shell Review
  - 当前 `ActionView` 可以描述为：
    - 模板消费
    - 核心 load 数据面 host
    - group/route/lifecycle bridge
  - 还不能描述为“极薄 page shell”

### 页面保留态白名单结论

- 本批结束后，暂时允许继续留在页面的状态：
  - `status`
  - `traceId`
  - `lastTraceId`
  - `records`
  - `listTotalCount`
  - `projectScopeTotals`
  - `projectScopeMetrics`
  - 与路由桥接直接相关的 filter/sort/viewMode/load 输入
- 已不应继续由页面直接声明的状态：
  - selection base state
  - batch base state
  - HUD entries 展示拼装
  - advanced rows 展示拼装

### Group Runtime 归宿结论

- `group runtime state` 当前归宿：
  - 状态层：runtime capsule
  - 触发层：page shell bridge
  - 展示层：模板消费
- 这意味着 group 不是“页面状态面污染”的主因，但仍是 page shell 继续变薄的主要阻塞项

### 验证结论

- 通过：
  - `make verify.frontend.typecheck.strict`
  - `make verify.product.final_slice_readiness_audit`
- 当前完成态：
  - `final_slice_readiness_audit` 仍为 `READY_FOR_SLICE`
  - 未引入新的前端业务推断
  - 未牵出后端 contract 改动

---

## Batch-B 收口判断

- Batch-B 已完成，不再建议继续在本批次追加小修
- 当前剩余问题已集中为：
  - `ActionView` 核心 load 数据面 host 仍在页面
  - `group runtime` 的 route/drilldown bridge 仍由页面承担
  - assembler 还不是唯一 page VM 主入口
- 这些问题已经超出“state host 收缩批次”的自然范围，应进入下一批单独定义
