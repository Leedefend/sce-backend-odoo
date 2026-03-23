# Second Slice Five-Layer Freeze

## 冻结对象

- 切片：`项目创建 -> 驾驶舱 -> 计划 -> 执行`
- 原则：五层职责固定，不允许跨层合并
- 状态：`正式冻结`

## L1 Model Layer

- `project.project`
- `project.task`
- `mail.activity`

### 冻结口径

- `project.project` 承载项目上下文与 `sc_execution_state`
- `project.task.sc_state` 作为执行任务业务真源
- `mail.activity(summary="执行推进跟进")` 作为最小 follow-up 承载

## L2 Domain Capability Layer

- `create_project`
- `initialize_project`
- `plan_bootstrap`
- `execution_enter`
- `execution_advance`

### 冻结口径

- 创建与初始化仍复用首发链真源
- 计划层只暴露最小准备度与下一跳调度，不返回前端结构推导
- 执行层只暴露最小 entry/runtime/action contract，不把任务状态机搬到前端

## L3 Scene Layer

- `projects.intake`
- `project.dashboard`
- `project.plan_bootstrap`
- `project.execution`

### 冻结口径

- 流转固定为：
  - `project.initiation -> project.dashboard -> project.plan_bootstrap -> project.execution`
- 不允许跳过 `dashboard` 和 `plan_bootstrap` 直接扩写第二切片主线

## L4 Contract Layer

- dashboard entry/block contract
- plan entry/block contract
- execution entry/block contract
- execution advance action contract

### 冻结口径

- scene entry 统一遵守 carrier：
  - `project_id`
  - `scene_key`
  - `scene_label`
  - `state_fallback_text`
  - `title`
  - `summary`
  - `blocks`
  - `suggested_action`
  - `runtime_fetch_hints`
- runtime block 统一保持：
  - `project_id`
  - `block_key`
  - `block`
  - `degraded`

## L5 Frontend Layer

- 创建页
- 驾驶舱页
- Scene 通用 contract consumer

### 冻结口径

- 前端只消费 scene entry / runtime block / action contract
- 不允许前端推导 execution state machine
- 不允许前端绕过 `project_id` 连续链重建场景语义

## 冻结结论

- 第二切片五层边界已经固定，可作为正式冻结切片继续发布。
