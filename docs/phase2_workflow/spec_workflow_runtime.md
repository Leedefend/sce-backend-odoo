# Workflow Runtime 规范（最小闭环）

面向 Phase 2 最小实现，覆盖四个动作：submit / approve / reject / cancel。先落地 `project.material.plan`，后续对象沿用同一规范。

## 状态字段建议

- 新增审批态字段（推荐）`approve_state`，保持原业务 `state` 兼容：
  - none（未走流程/旧数据）
  - submitted
  - approved
  - rejected
- 完成时再写入业务 state（如 confirmed/done），以免破坏 Phase1 逻辑。

## 动作语义

### submit
- 触发：经办（cap_material_user）
- 行为：
  - 创建 workflow_instance（model/res_id 关联）
  - 生成首个 workitem（指向审批节点）
  - 写 `approve_state = submitted`
  - 业务明细锁定
  - 记 log（submit，actor，时间，note 可空）

### approve
- 触发：审批人（cap_material_manager）
- 行为：
  - 完成当前 workitem，指派/生成下个 workitem
  - 若无下个节点：`approve_state = approved`，同步业务 state（如 confirmed）
  - 记 log（approve，actor，时间）

### reject
- 触发：审批人（cap_material_manager）
- 行为：
  - 终止当前 instance（或重置到起点）
  - 写 `approve_state = rejected`（可同时回写业务 state = draft）
  - 清除/关闭当前及后续 workitem
  - 记 log（reject，actor，时间，note）

### cancel
- 触发：经办/管理员（按业务域配置）
- 行为：
  - 将 instance 标记为 cancelled
  - 关闭所有未完成 workitem
  - 写 `approve_state = none` 或保持业务 state = cancel
  - 记 log（cancel，actor，时间）

## 权限原则

- 所有动作必须在后端 `has_group` 校验（能力组），UI 仅作提示。
- workitem 分配支持：
  - 指定用户（assigned_to）
  - 指定能力组（assigned_group_xmlid），运行时匹配成员。

## 日志与追溯

- 每个动作必写 `sc_workflow_log`，最少字段：instance、action、actor、note、created_at。
- 业务模型可在表单页签或 chatter 中展示 log 以便审计。

## 兼容性要求

- 不改原 state 流程，审批态独立存储，避免 Phase1 数据/视图破坏。
- 工作流失败/驳回时，业务记录可回到 draft，并释放明细编辑。*** End Patch
