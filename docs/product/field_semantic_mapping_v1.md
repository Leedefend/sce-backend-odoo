# 字段语义映射 v1

## 1. 范围

本映射用于展示层产品化翻译，覆盖：状态、布尔、阶段、金额、百分比。

## 2. 技术值 -> 产品语义值

## 2.1 状态字段

- `draft` -> 草稿
- `open` / `active` / `in_progress` / `01_in_progress` -> 进行中
- `done` / `approved` / `paid` -> 已完成
- `pending` / `todo` / `to_do` -> 待处理
- `blocked` / `overdue` / `risk` / `high_risk` -> 风险
- `cancel` / `cancelled` / `rejected` -> 已取消/已驳回

## 2.2 布尔字段

- `true` -> 是
- `false` -> 否

## 2.3 阶段字段

- 阶段值优先按状态映射处理；
- 若为中文阶段名称，直接展示原值。

## 2.4 金额字段

- 数值展示：
  - `>= 1e8` -> `x.xx亿`
  - `>= 1e4` -> `x.xx万`
  - 其他 -> 保留两位小数

## 2.5 百分比字段

- `*_percent` / `*_rate` -> `N%`

## 3. 前后端处理边界

- 前端展示层处理（本轮已接入）：
  - 状态中文化
  - 布尔中文化
  - 金额友好化
  - 百分比格式化
- 后端 contract 层（本轮不改）：
  - 核心枚举与原始字段保持技术值
  - 不改 contract envelope

## 4. 本轮已接入页面

- `project.management`
- `projects.ledger`
- `projects.list`
- `task.center`
- `risk.center`
- `cost.project_boq`

## 5. 后续建议统一字段类型

- 风险等级字段（`risk_level`/`severity`）
- SLA/时效字段（`deadline_status`）
- 审批状态字段（`approval_state`）
