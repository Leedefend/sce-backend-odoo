# 主数据字段绑定审计 v1

## 审计范围

- 企业主数据：`res.company`、`hr.department`、`res.users`、`sc.enterprise.post`
- 业务主数据：`project.project`、`payment.request`、`sc.settlement.order`、`project.budget`、`project.cost.ledger`

## 字段绑定结果（静态）

| 业务对象 | 模型侧字段证据 | 视图侧字段证据 | 结果 | 备注 |
|---|---|---|---|---|
| `res.company` | `models/res_company.py` 定义 `sc_short_name/sc_credit_code/sc_department_count` | `views/res_company_views.xml` 引用公司扩展字段 | PASS | 公司→组织入口动作存在。 |
| `hr.department` | `models/hr_department.py` 定义 `company_id/sc_manager_user_id/sc_user_count` | `views/hr_department_views.xml` 引用并提供搜索分组 | PASS | 同公司约束已在 `@api.constrains`。 |
| `res.users` | `models/res_users.py` 定义 `sc_department_id/sc_post_id/...` | `views/res_users_views.xml` 引用主/附加部门与岗位字段 | PASS | 用户主数据页与企业基座一致。 |
| `sc.enterprise.post` | `models/sc_enterprise_post.py` 定义岗位核心字段 | `res_users` 视图间接消费 `sc_post_id/sc_post_ids` | PASS | 岗位模型与用户绑定成立。 |
| `payment.request` | `models/core/payment_request.py` 含 `settlement_*`、`paid_amount_total` 等字段 | `views/core/payment_request_views.xml` 逐项引用 | PASS | 付款与结算联动字段完备。 |
| `sc.settlement.order` | `models/core/settlement_order.py` 含 `amount_paid/amount_payable/compliance_*` | `views/core/settlement_views.xml` 引用状态与合规字段 | PASS | 结算单字段链路完整。 |
| `project.budget` | `models/core/project_budget.py`（已注册） | `views/core/project_budget_views.xml` + 快捷 action | PASS_WITH_RISK | ACL 出现重复 manager 行，见风险。 |
| `project.cost.ledger` | `models/core/cost_domain.py`（台账对象） | `views/core/cost_domain_views.xml` / 项目页快捷入口 | PASS | 成本台账入口已挂到项目页。 |

## 发现的风险点

1. `project.budget` 在 `ir.model.access.csv` 发现重复 manager ACL 行（同模型同权限面重复）。
2. 项目/任务/预算/成本对象在 `sc_record_rules.xml` 规则覆盖较少（关键财务对象覆盖充分）。

## 结论

- 原生字段绑定在静态层面整体成立，未发现明显“视图字段找不到模型字段”的硬断裂。
- 建议 Batch B 对 `project.budget` ACL 重复项与关键对象规则覆盖做最小修复。

