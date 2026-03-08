# Owner Management Template Draft v1

## 目标能力分组

- 项目监督（project oversight）
- 合同执行监控（contract execution）
- 投资控制（investment control）
- 支付审核（payment approval）
- 风险预警（risk early warning）

## 目标首页 Scene

- owner.dashboard
- contracts.monitor
- payments.approval
- risk.center

## 角色矩阵（草案）

- owner_manager: 首页=owner.dashboard, 高频=contracts.monitor,payments.approval
- owner_finance: 首页=payments.approval, 高频=cost.control,contracts.monitor
- owner_exec: 首页=owner.dashboard, 高频=risk.center,projects.dashboard

## 迁移原则

- 不改底层五层架构
- 通过 capability + scene 重编排实现业主管理模式
- 前端入口按 governed surface 消费，不绕过 contract
