# 导航分组标准词表 v1

> Scope: scene nav 分组（`group_key`）显示名标准。

## 说明
- 本词表用于约束导航分组命名，避免同义词和临时文案漂移。
- 前端展示名以本词表为准；新增分组需同步更新中英文版本。
- 英文版：`docs/architecture/nav_group_terms_v1.en.md`

## 标准映射（CN/EN）
| group_key | 中文标准名 | English Standard Name |
|---|---|---|
| portal | 工作台 | Workbench |
| projects | 项目管理 | Project Management |
| task | 任务管理 | Task Management |
| risk | 风险管理 | Risk Management |
| cost | 成本管理 | Cost Management |
| contract | 合同管理 | Contract Management |
| finance | 资金财务 | Finance |
| data | 数据与字典 | Data & Dictionary |
| config | 配置中心 | Configuration Center |
| contracts | 合同履约 | Contract Performance |
| payments | 收付款 | Receivables & Payables |
| my_work | 我的工作 | My Work |
| portfolio | 项目组合 | Project Portfolio |
| quality | 质量管理 | Quality Management |
| safety | 安全管理 | Safety Management |
| resource | 资源调配 | Resource Allocation |
| delivery | 交付管理 | Delivery Management |
| operation | 经营总览 | Operations Overview |
| workspace | 工作空间 | Workspace |
| others | 其他场景 | Other Scenes |

## 使用规则
- `group_key` 稳定优先，不随展示文案变化。
- 中文命名要求“业务域 + 管理/中心/总览”风格统一。
- 避免重名：同一导航层级下不出现相同分组名。
