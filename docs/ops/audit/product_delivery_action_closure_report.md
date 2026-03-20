# Product Delivery Action Closure Smoke

- target_count: 3
- pass_count: 2
- failed_count: 1
- error_count: 1

## Checks

- 付款申请与审批 (finance.payment_requests): FAIL issues=search_filters<1
- 项目台账 (projects.list): PASS issues=-
- 预算管理 (cost.project_budget): PASS issues=-
