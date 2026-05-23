---
capability_stage: P0.1
status: active
---
# 功能索引

这是面向客户、销售、实施和支持团队的产品能力目录。它不以技术模块为主线，而以客户能理解的业务价值、目标角色、产品版本和验收方式为主线。

| 产品能力 | 目标角色 | 客户价值 | 入口/场景 | 版本 | 状态 | 验收方式 |
| --- | --- | --- | --- | --- | --- | --- |
| 我的工作 | 全角色 | 聚合待办、关注项目、快捷入口和风险提醒 | `my_work.workspace` | standard | 已交付 | 角色登录后进入默认工作区，无空跳转 |
| 项目立项与台账 | 项目经理、经营人员 | 统一项目创建、基础资料和项目清单 | `projects.intake`, `projects.list` | standard | 已交付 | 新建/查看项目，列表可搜索筛选 |
| 项目驾驶舱 | 项目经理、领导 | 查看项目基本信息、进度、合同、成本、资金、风险 | `projects.dashboard` | standard | 已交付 | 从项目台账进入驾驶舱，关键区块可渲染 |
| 项目执行协同 | 项目经理 | 跟踪任务、计划、周报和执行推进 | `projects.execution`, `project.task.board` | standard | 已交付 | 任务列表与项目上下文一致 |
| 合同中心 | 项目经理、经营人员 | 管理收入合同、支出合同和合同执行信息 | `contract.center` | standard | 已交付 | 合同列表字段语义正确，关联项目可追溯 |
| 成本预算 | 项目经理、财务 | 建立项目预算、成本台账和成本偏差分析 | `cost.project_budget`, `cost.project_cost_ledger` | pro | 已交付 | 预算与成本台账可按项目查看 |
| 利润分析 | 领导、财务 | 比较收入、成本、利润和异常指标 | `cost.profit_compare` | pro | 已交付 | 指标页面有业务数据或明确空状态 |
| 付款申请 | 项目经理、财务 | 发起、审批、跟踪付款申请 | `finance.payment_requests` | pro | 已交付 | 草稿、提交、审批状态可见，动作受权限控制 |
| 资金台账 | 财务 | 查看支付、资金和对账事实 | `finance.payment_ledger`, `finance.treasury_ledger` | pro | 已交付 | 付款事实可追溯到项目和申请 |
| 结算管理 | 财务、项目经理 | 管理结算单、结算结果和合同履约闭环 | `finance.settlement_orders` | pro | 已交付 | 结算记录能按项目/合同查询 |
| 采购与物资 | 采购经理、项目经理 | 管理物资目录、采购申请、入库和出库 | `material.center`, `material.procurement` | pro | 已交付 | 物资目录与采购记录可打开 |
| 劳务资源 | 采购经理、项目经理 | 管理劳务计划、申请、考勤和结算 | `labor.request`, `labor.attendance` | enterprise | 预览 | 入口可见性受版本控制 |
| 机械设备 | 采购经理、项目经理 | 管理设备计划、申请、使用和结算 | `equipment.request`, `equipment.usage` | enterprise | 预览 | 入口可见性受版本控制 |
| 分包协同 | 采购经理、项目经理 | 管理分包申请、登记、结算和价格 | `subcontract.request`, `subcontract.settlement` | enterprise | 预览 | 入口可见性受版本控制 |
| 质量安全 | 项目经理、领导 | 管理质量问题、安全问题和整改闭环 | `quality.center`, `safety.center` | enterprise | 预览 | 问题列表和整改状态可查询 |
| 经营指标 | 领导 | 查看企业经营指标、异常和重点项目 | `portal.dashboard`, `finance.operating_metrics` | pro | 已交付 | 只读角色可查看指标，无越权动作 |
| 能力治理 | 管理员 | 查看产品能力、场景、发布策略和治理状态 | `portal.capability_matrix` | pro | 已交付 | 能力矩阵与发布状态一致 |
| 配置中心 | 配置管理员 | 管理菜单、字典、业务配置和可见范围 | `data.dictionary`, `menu.config` | enterprise | 已交付 | 配置变更有权限控制和审计入口 |
| 授权与版本 | 管理员、客户成功 | 解释当前产品版本、开放能力和升级限制 | `release.operator`, `license.status` | enterprise | 待完善 | 授权状态、不可用原因、升级路径可见 |
| Demo 数据包 | 销售、实施 | 用于演示、培训和样例验收 | `smart_construction_demo` | demo | 仅演示 | 生产默认不安装，可重置演示数据 |

## 说明
- `standard` 面向基础项目管理闭环。
- `pro` 面向财务、成本、经营指标等增强协同。
- `enterprise` 面向多资源、多角色、配置治理和高级授权。
- `demo` 仅用于销售演示和培训，不进入生产默认安装。
