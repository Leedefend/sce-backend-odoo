# Second Slice Product Contract

## 定位

- 产品：`施工企业项目管理系统（第二切片）`
- 切片：`项目创建 -> 驾驶舱 -> 计划 -> 执行`
- 本文性质：`冻结准备态产品口径`

## 用户路径

1. 进入项目创建页并提交最小字段。
2. 系统初始化项目骨架并进入 `project.dashboard`。
3. 用户从 dashboard `next_actions` 进入 `project.plan_bootstrap`。
4. 用户从 plan `next_actions` 进入 `project.execution`。
5. 用户执行 `project.execution.advance`，看到最小状态推进结果。

## 只承诺什么

- 创建项目
- 进入驾驶舱
- 查看计划准备度
- 进入执行场景
- 执行最小状态推进

## 当前承载

### Dashboard

- `progress`
- `risks`
- `next_actions`

### Plan

- `plan_summary_detail`
- `plan_tasks`
- `next_actions`

### Execution

- `execution_tasks`
- `pilot_precheck`
- `next_actions`

## 执行推进口径

- 公共动作：`project.execution.advance`
- 结果只允许：
  - `success`
  - `blocked`
- 状态机只允许：
  - `ready -> in_progress`
  - `in_progress -> done`
  - `blocked -> ready`

## 明确不包含

- 成本闭环
- 合同付款
- 结算分析
- 浏览器级第二切片证据

## 当前判断

- 第二切片已具备 `guard + flow + action/state` 主链证据。
- 当前处于：`冻结准备态`
- 下一步如需升级为正式冻结，仍需补浏览器级证据与最终收口文档。
