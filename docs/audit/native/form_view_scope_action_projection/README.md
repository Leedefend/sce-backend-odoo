# Form View Scope Action Projection Audit

- audit_login: wutao
- sample_count: 30
- pass_count: 30
- fail_count: 0
- explicit_source_view_count: 8
- field_policy_scope_count: 0

| status | model | action | source_view | projection_scope | policies | issues |
|---|---|---|---:|---|---:|---|
| pass | `project.project` | `696:项目立项` | 1463 | `action:696:project.project:form:view:1463` | 0 |  |
| pass | `project.project` | `697:快速创建项目` | 1464 | `action:697:project.project:form:view:1464` | 0 |  |
| pass | `project.project.stage` | `325:项目阶段` | 899 | `action:325:project.project.stage:form:view:899` | 0 |  |
| pass | `res.partner` | `314:供应商` | 1514 | `action:314:res.partner:form:view:1514` | 0 |  |
| pass | `res.partner` | `786:客户` | 1511 | `action:786:res.partner:form:view:1511` | 0 |  |
| pass | `res.partner` | `787:供应商` | 1514 | `action:787:res.partner:form:view:1514` | 0 |  |
| pass | `res.users` | `69:用户` | 162 | `action:69:res.users:form:view:162` | 0 |  |
| pass | `res.users` | `723:用户账号与权限` | 1835 | `action:723:res.users:form:view:1835` | 0 |  |
| pass | `construction.contract` | `562:项目合同汇总` | 0 | `action:562:construction.contract:form:view:0` | 0 |  |
| pass | `construction.contract.expense` | `579:支出合同` | 0 | `action:579:construction.contract.expense:form:view:0` | 0 |  |
| pass | `construction.contract.expense` | `752:支出合同执行` | 0 | `action:752:construction.contract.expense:form:view:0` | 0 |  |
| pass | `construction.contract.expense` | `799:材料合同` | 0 | `action:799:construction.contract.expense:form:view:0` | 0 |  |
| pass | `construction.contract.expense` | `800:正常合同` | 0 | `action:800:construction.contract.expense:form:view:0` | 0 |  |
| pass | `construction.contract.expense` | `801:劳务合同` | 0 | `action:801:construction.contract.expense:form:view:0` | 0 |  |
| pass | `construction.contract.expense` | `802:租赁合同` | 0 | `action:802:construction.contract.expense:form:view:0` | 0 |  |
| pass | `construction.contract.expense` | `803:分包合同` | 0 | `action:803:construction.contract.expense:form:view:0` | 0 |  |
| pass | `construction.contract.expense` | `804:其他合同` | 0 | `action:804:construction.contract.expense:form:view:0` | 0 |  |
| pass | `construction.contract.expense` | `805:补充合同` | 0 | `action:805:construction.contract.expense:form:view:0` | 0 |  |
| pass | `construction.contract.income` | `578:收入合同` | 0 | `action:578:construction.contract.income:form:view:0` | 0 |  |
| pass | `construction.contract.income` | `751:收入合同执行` | 0 | `action:751:construction.contract.income:form:view:0` | 0 |  |
| pass | `construction.work.breakdown` | `563:工程结构` | 0 | `action:563:construction.work.breakdown:form:view:0` | 0 |  |
| pass | `hr.department` | `705:组织架构` | 0 | `action:705:hr.department:form:view:0` | 0 |  |
| pass | `payment.method` | `242:付款方式` | 0 | `action:242:payment.method:form:view:0` | 0 |  |
| pass | `payment.request` | `671:付款申请` | 0 | `action:671:payment.request:form:view:0` | 0 |  |
| pass | `payment.request` | `672:收款申请` | 0 | `action:672:payment.request:form:view:0` | 0 |  |
| pass | `payment.request.line` | `624:付款申请明细` | 0 | `action:624:payment.request.line:form:view:0` | 0 |  |
| pass | `project.boq.line` | `522:工程量清单` | 0 | `action:522:project.boq.line:form:view:0` | 0 |  |
| pass | `project.budget` | `507:项目预算` | 0 | `action:507:project.budget:form:view:0` | 0 |  |
| pass | `project.budget.cost.alloc` | `513:预算清单分摊` | 0 | `action:513:project.budget.cost.alloc:form:view:0` | 0 |  |
| pass | `project.cost.code` | `508:成本科目` | 0 | `action:508:project.cost.code:form:view:0` | 0 |  |
