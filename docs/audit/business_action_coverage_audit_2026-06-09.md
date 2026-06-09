# Business Action Coverage Audit 2026-06-09

## Scope

在业务闭环专项之后，继续验证用户确认正式菜单中的高频办理入口是否具备可执行的正式模型动作。

本轮覆盖：

- 付款执行：确认、登记付款、付款申请联动完成、付款台账生成
- 收入登记：确认、登记收款、收款申请联动完成
- 公司财务支出/费用单：提交、批准、完成、付款申请联动完成
- 发票登记：确认、登记
- 抵扣登记：确认、抵扣
- 项目管理人员工资登记：提交、完成、月份规则拦截
- 资金账户操作：确认、完成

## Command

```bash
DB_NAME=sc_demo scripts/ops/validate_business_action_coverage.sh
```

## Result

```text
BUSINESS_ACTION_COVERAGE_AUDIT: {"audit": "business_action_coverage_audit", "coverage": {"expense_claim": {"claim": 271739, "payment_request": 35836, "settlement": 2776}, "fund_account_operation": {"operation": 90358, "source_account": 2653, "target_account": 2654}, "hr_payroll": {"payroll": 11196}, "invoice_registration": {"invoice": 774904}, "payment_execution": {"execution": 170323, "payment_request": 35834, "settlement": 2775}, "receipt_income": {"payment_request": 35835, "receipt": 351015}, "tax_deduction": {"deduction": 10238}}, "failures": [], "status": "PASS"}
```

## Notes

- 脚本只创建专项审计数据并调用正式模型动作，不修改菜单体系，不覆盖用户已确认数据。
- 付款执行、费用支出类付款按正式规则补齐结算单锚点后再生成付款台账。
- 审计过程中保留负向校验：重复确认、未补齐锚点、无效工资月份等场景必须被业务模型拦截。
