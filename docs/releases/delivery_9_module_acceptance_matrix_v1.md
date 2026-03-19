# 9 模块上线前验收矩阵 v1

## 说明
- 本矩阵用于交付封板验收，不用于功能规划。
- 状态定义：`PASS` / `FAIL` / `PENDING`。

| 模块 | 关键场景入口 | 关键角色 | 前置数据 | 必跑验证 | 状态 |
|---|---|---|---|---|---|
| 项目管理 | `projects.list` / `projects.ledger` / `projects.intake` | PM/老板 | 项目主数据 | scene contract + 列表/表单 smoke | PENDING |
| 项目驾驶舱 | `project.management` / `portal.dashboard` | 老板/PM | 项目+风险聚合 | dashboard contract + role journey | PENDING |
| 合同管理 | `contract.center` / `contracts.workspace` | 合同经理/老板 | 合同主数据 | contract guard + 合同异常流程 | PENDING |
| 成本管理 | `cost.*` | 成本经理/PM | 预算/台账/进度 | list/action/batch smoke | PENDING |
| 资金财务 | `finance.*` / `payments.*` | 财务经理 | 收付款/结算数据 | finance journey + settlement guard | PENDING |
| 风险管理 | `risk.center` / `risk.monitor` | PM/老板 | 风险动作数据 | risk flow smoke + escalation check | PENDING |
| 任务管理 | `task.center` / `my_work.workspace` | 全角色 | 工作项数据 | workitem query + action closure | PENDING |
| 数据与字典 | `data.dictionary` | 配置/实施 | 业务字典 | dictionary CRUD smoke | PENDING |
| 配置中心 | `config.project_cost_code` | 配置管理员 | 成本科目主数据 | config read/write smoke | PENDING |

## 验收通过条件
- 9 个模块全部从 `PENDING/FAIL` 收敛到 `PASS`。
- 每个模块至少附 1 条 system-bound 证据（命令、DB、commit、结果）。

