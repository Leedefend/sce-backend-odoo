# Construction Enterprise Template v1

## 默认角色集合

- construction_manager
- project_manager
- finance_manager
- risk_manager

## 默认 Scene 集合

- projects.dashboard
- projects.execution
- projects.detail
- contracts.monitor
- cost.control
- payments.approval
- risk.center
- my_work.workspace

## 默认 Capability Groups

- project_management
- contract_management
- cost_management
- finance_management
- analytics
- governance

## 首页入口布局

- 我的工作
- 核心场景入口
- 关键风险
- 经营驾驶舱
- 能力快捷入口

## 角色入口策略

以下策略来自 role_scene_matrix_v1：

- construction_manager: home=projects.dashboard, 高频=projects.dashboard,contracts.monitor,cost.control
- project_manager: home=projects.execution, 高频=projects.execution,projects.detail,my_work.workspace
- finance_manager: home=payments.approval, 高频=payments.approval,cost.control,contracts.monitor
- risk_manager: home=risk.center, 高频=risk.center,my_work.workspace,projects.detail
