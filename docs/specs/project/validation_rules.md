# Project Lifecycle Validation Rules

目标：草稿态允许不完整信息，业务必填校验集中在状态跃迁（立项）动作。

## 状态与校验口径

- `draft`（草稿）：允许字段为空，仅保留结构性必填（如 `name`）。
- `in_progress`（立项/进入在建）：触发项目业务必填校验。

## 立项必填字段（draft -> in_progress）

- `owner_id`：业主单位
- `manager_id`：项目经理
- `location`：项目地点

说明：
- 上述字段在模型层不设 `required=True`，统一由 `_sc_validate_for_transition` 校验。
- 其他强制校验（如 BOQ 是否导入、结算/付款门禁）仍由原有 Guard 负责。

## 实现入口

- `project.project._sc_validate_for_transition(target_state)`
- `project.project._validate_lifecycle_transition(target_state)` 在 `draft -> in_progress` 时调用

## 验收

- 草稿项目可保存不完整信息
- 立项（状态切换到 `in_progress`）时缺字段报 `ValidationError`
- 补齐必填字段后可成功立项
