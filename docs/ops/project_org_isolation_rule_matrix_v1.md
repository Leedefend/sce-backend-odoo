# 项目组织与隔离规则矩阵 v1

| 对象 | 组织事实 | 隔离锚点 | 本轮验证方式 | 当前状态 |
|---|---|---|---|---|
| `project.project` | 主责岗位 + 项目成员入口 | `company_id` | `native_business_fact_isolation_anchor_verify` + full-chain | PASS |
| `project.task` | 项目成员/负责人 | `company_id`,`project_id` | role operability + role alignment | PASS |
| `project.budget` | 项目预算责任域 | `company_id`,`project_id` | role operability + anchor verify | PASS |
| `project.cost.ledger` | 项目成本责任域 | `company_id`,`project_id` | role operability + anchor verify | PASS |
| `payment.request` | 付款流程责任域 | `company_id`,`project_id` | role operability + anchor verify | PASS |
| `payment.ledger` | 付款台账责任域 | `company_id`,`project_id` | anchor verify | PASS |
| `sc.settlement.order` | 结算流程责任域 | `company_id`,`project_id` | role operability + anchor verify | PASS |

## 高风险待办（闸门后执行）
- `project.budget` 重复 ACL 修复（`ir.model.access.csv`）。
- `project.project/task/budget/cost.ledger` 最小 record rule 补齐（`record_rules/**`）。
- 付款/结算对象细粒度 record rule 统一（`record_rules/**`）。
