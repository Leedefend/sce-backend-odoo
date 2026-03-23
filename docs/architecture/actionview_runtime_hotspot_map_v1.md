# ActionView Runtime Hotspot Map v1

## 目的

- 为 Phase 2 Batch-A Step 1 提供真实热点地图
- 替换旧库存中已失真的 `ActionView` 行号与职责判断
- 明确后续拆分顺序：`load -> action -> batch -> assembler`

## 文件对象

- [ActionView.vue](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/views/ActionView.vue)
- [useActionPageModel.ts](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/app/assemblers/action/useActionPageModel.ts)

## 现状判断

- `ActionView` 已明显进入 runtime/composable 拆分中段
- 页面不再直接持有单个巨大 `load()` 函数
- 但页面仍是总装配中心：
  - 大状态面仍在页面
  - runtime 模块仍由页面逐个接线
  - page assembly 还没有真正吞掉 runtime glue

## 热点分区

### 1. Page State Host

- 位置：
  - [ActionView.vue](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/views/ActionView.vue#L777)
- 特征：
  - 页面集中持有 `status`、`traceId`、`records`、`selectedIds`、`batchMessage`、`batchBusy`
  - group runtime capsule 也由页面初始化
- 判断：
  - 这是当前 `ActionView` 最大的 page state center
  - 属于 Batch-A 必拆区

### 2. Page Assembly Entry

- 位置：
  - [useActionPageModel.ts](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/app/assemblers/action/useActionPageModel.ts)
  - [ActionView.vue](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/views/ActionView.vue#L1295)
- 特征：
  - 已存在 VM assembler
  - 但页面仍在 assembler 之前完成大量 runtime glue 与状态汇总
- 判断：
  - assembler 已形成雏形
  - 但还不是总入口
  - Batch-A 终点应让这里变成唯一 page assembly 主入口

### 3. Runtime Orchestration Glue

- 位置：
  - [ActionView.vue](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/views/ActionView.vue#L1352)
  - [ActionView.vue](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/views/ActionView.vue#L1605)
  - [ActionView.vue](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/views/ActionView.vue#L2117)
- 特征：
  - 页面连接 navigation / route preset / group runtime / request context / header runtime / action runtime / batch runtime
  - 这些模块本身已拆出，但仍通过页面串联
- 判断：
  - 当前问题不是“模块不存在”
  - 而是“页面仍是 orchestration bus”

### 4. Load Facade Wiring

- 位置：
  - [ActionView.vue](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/views/ActionView.vue#L2071)
  - [ActionView.vue](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/views/ActionView.vue#L2083)
  - [ActionView.vue](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/views/ActionView.vue#L2237)
- 特征：
  - `useActionViewLoadFacadeRuntime` 已存在
  - 但页面通过 `loadPageInvoker/requestLoadPage` 把 load 分发给多个 runtime 调用点
- 判断：
  - `load` 已不是“函数没拆”
  - 但仍未完成“调用面统一”
  - Step 2 应优先收这里

### 5. Action Runtime Wiring

- 位置：
  - [ActionView.vue](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/views/ActionView.vue#L1605)
- 特征：
  - `useActionViewActionRuntime` 已承担真正执行逻辑
  - 但页面仍向它注入大量路由、mutation、refresh、record context、button request 依赖
- 判断：
  - Action 逻辑本体已拆
  - 仍缺单一 facade 边界
  - Step 3 应处理这里

### 6. Batch Runtime Wiring

- 位置：
  - [ActionView.vue](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/views/ActionView.vue#L2117)
- 特征：
  - `useActionViewBatchRuntime` 已承担批量执行
  - 但页面仍注入大量 request context、artifact、error fallback、message resolver
- 判断：
  - batch 是当前最重的一块 glue 面
  - Step 4 应单独拆 capsule/facade

## 新库存结论

- 旧库存里“ActionView 仍是单文件 load/action/batch 巨石”的判断已经部分过时
- 新的准确表述应是：
  - `ActionView` 是一个“runtime facade 注入中心 + page state center”
  - 而不是“所有逻辑都写在一个函数里”

## Batch-A 建议拆分顺序

1. 先校准库存与职责图
2. 收 `loadPageInvoker/requestLoadPage` 调用面
3. 收 `runContractAction` facade 注入面
4. 收 `batch runtime` 注入面
5. 最后把 VM 入口收敛到 assembler

## Batch-B 现状补充

- Batch-A 完成后，以下热点已经不再成立为主问题：
  - `loadPageInvoker/requestLoadPage` 页面总线
  - action 副作用直接挂在 `useActionViewActionRuntime`
  - batch 副作用直接挂在 `useActionViewBatchRuntime`
- Batch-B 当前更准确的热点是：
  - 页面仍保留核心 state host：
    - `status`
    - `traceId`
    - `records`
    - `group runtime state`
  - assembler 已开始接管更多展示拼装：
    - `advanced rows`
    - `hud entries`
  - selection/batch 基础状态已收进 capsule，但 group runtime 仍通过 page shell 连接 route/trigger

## Batch-B 归宿判断

- 已进入 runtime capsule：
  - selection state
  - batch base state
  - group state
- 已进入 assembler：
  - advanced rows
  - hud entries
- 仍留在页面，且暂时合理：
  - route bridge
  - lifecycle trigger
  - load 主状态
  - records 主数据面
- 仍需下一批继续压缩：
  - group runtime bridge
  - 以 `records/status/trace` 为中心的页面 host
