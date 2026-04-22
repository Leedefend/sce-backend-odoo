# 角色-能力-ACL-记录规则矩阵 v1

## 1) 角色与能力组层次（静态）

- 基础能力组：`group_sc_internal_user`（唯一 implied `base.group_user`）
- 能力域：`project/material/purchase/finance/contract/cost/settlement/data/config`（读/用户/管理分层）
- 角色桥接：`group_sc_role_bridge_*` -> `group_sc_role_*`（角色通过桥接 implied 到能力组）

## 2) 关键模型 ACL 覆盖（来自 `ir.model.access.csv`）

| 模型 | ACL 条目数 | 典型组 | 结论 |
|---|---:|---|---|
| `project.project` | 4 | `project_read/user/manager/super_admin` | 覆盖完整 |
| `project.task` | 4 | `project_read/user/manager/super_admin` | 覆盖完整 |
| `payment.request` | 3 | `finance_read/user/manager` | 覆盖完整 |
| `payment.ledger` | 3 | `finance_read/user/manager` | 覆盖完整 |
| `sc.settlement.order` | 6 | `settlement_read/user/manager` + read 组合 | 覆盖较重 |
| `project.budget` | 3 | `cost_read/manager` | 存在 manager 重复行 |
| `project.cost.ledger` | 3 | `cost_read/user/manager` | 覆盖完整 |

## 3) 记录规则覆盖（来自 `sc_record_rules.xml`）

| 模型 | 规则条数 | 规则类型 |
|---|---:|---|
| `payment.request` | 3 | read/user/manager 按项目成员域 |
| `payment.ledger` | 3 | read/user/manager 按项目成员域 |
| `sc.settlement.order` | 3 | read/user/manager |
| `project.project` | 0 | 未在该文件中显式定义 |
| `project.task` | 0 | 未在该文件中显式定义 |
| `project.budget` | 0 | 未在该文件中显式定义 |
| `project.cost.ledger` | 0 | 未在该文件中显式定义 |

## 4) 审计判断

- 财务链（付款/台账/结算）规则约束相对完整。
- 项目/任务/预算/成本台账主要靠 ACL 与业务逻辑约束，记录规则显式面偏弱。

## 5) Batch B 最小修复建议

1. 去重 `project.budget` 重复 ACL 行。
2. 对项目/任务/预算/成本台账补最小必要 record rule（仅补闭环必需）。
3. 固定“角色->能力->ACL->规则”排错顺序，避免桥接层误判。

