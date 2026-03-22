# Product v0.1 Overview

## Goal
- 将当前项目生命周期主链收口为第一个可交付产品：可进入、可流转、可推进、可验证。

## Scope
- `project.initiation.enter`
- `project.dashboard.enter`
- `project.plan_bootstrap.enter`
- `project.execution.enter`
- `project.execution.advance`

## Product Shape
- 启动链保持 `boot + preload + runtime fetch` 三层分离。
- 场景入口保持 `entry(minimal) + runtime blocks + suggested_action`。
- 产品主链保持 `initiation -> dashboard -> plan_bootstrap -> execution -> execution.advance`。

## User Value
- 用户能从立项进入完整生命周期工作面。
- 每个场景都能看到当前状态与下一步动作。
- 执行推进后能看到状态变化，并知道后续动作。

## Odoo Alignment
- 执行任务区块基于 `project.task`。
- 执行推进记录进入 `project.project` chatter。
- 执行推进后的待跟进动作进入 `mail.activity`。

## Runtime Structure
- Entry 只返回最小可渲染 contract。
- 重数据通过 runtime block fetch 获取。
- Block 失败独立降级，不升级为整页错误。

## Acceptance Signals
- `system.init` preload latency 回到预算内。
- 产品四场景文案与状态表达统一。
- `execution.advance` 返回 `from_state -> to_state`，并可在 UI 中可视化。
- 全链 smoke 与 contract guards 纳入基线。
