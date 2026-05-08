# Business Expense Fact Taxonomy v1

## Principle

Expense is not a single business object. The user-facing taxonomy follows the
source business fact and keeps each fact in its own lane:

- contract and purchase commitment facts stay in the contract center;
- payment request, request line, actual outflow, and payment residual facts stay
  in payment facts;
- expense reimbursement and deposit facts stay in expense/deposit facts;
- deduction, tax deduction, and fund confirmation facts stay in adjustment/tax
  facts;
- account, fund daily, financing, and borrowing facts stay in fund/account
  facts.

No menu in this taxonomy promotes historical facts into new payment,
settlement, treasury, or accounting workflow state.

## User-Facing Split

| Business fact | User-facing entry | Carrier |
| --- | --- | --- |
| Expense contract | 支出合同台账 | `construction.contract.expense` |
| Supplier contract pricing | 供应商合同计价事实 | `sc.legacy.supplier.contract.pricing.fact` |
| Legacy purchase/general contract | 历史采购/一般合同事实 | `sc.legacy.purchase.contract.fact` |
| Payment request | 付款申请 | `payment.request`, `type = pay` |
| Payment request line | 付款申请明细 | `payment.request.line` |
| Actual outflow | 实付登记 | `sc.payment.execution`, `source_kind = actual_outflow` |
| Payment request residual | 付款申请残余事实 | `sc.payment.execution`, `source_kind = outflow_request` |
| Legacy payment residual | 历史付款残余事实 | `sc.legacy.payment.residual.fact` |
| Expense reimbursement | 费用报销单 | `sc.expense.claim`, `claim_type = expense` |
| Deposit payment | 保证金支付 | `sc.expense.claim`, `claim_type = deposit_pay` |
| Deposit refund | 保证金退回 | `sc.expense.claim`, `claim_type = deposit_refund` |
| Deposit receive | 保证金收取 | `sc.expense.claim`, `claim_type = deposit_receive` |
| Legacy expense/deposit outflow | 历史费用/保证金流出 | `sc.legacy.expense.deposit.fact`, `direction = outflow` |
| Legacy expense/deposit refund | 历史费用/保证金流入退回 | `sc.legacy.expense.deposit.fact`, `direction = inflow_or_refund` |
| Legacy reimbursement line | 历史费用报销明细 | `sc.legacy.expense.reimbursement.line` |
| Deduction / settlement adjustment | 扣款/结算调整 | `sc.legacy.deduction.adjustment.line` |
| Tax deduction | 抵扣税额 | `sc.legacy.tax.deduction.fact` |
| Fund confirmation | 资金确认 | `sc.legacy.fund.confirmation.line` |
| Financing loan registration | 贷款登记 | `sc.financing.loan`, `loan_type = loan_registration` |
| Borrowing request | 借款申请 | `sc.financing.loan`, `loan_type = borrowing_request` |

## Acceptance

Acceptance database: `sc_partner_acceptance`.

Upgrade command:

```bash
docker exec sc-backend-odoo-partner-acceptance-odoo-1 \
  odoo -d sc_partner_acceptance -c /var/lib/odoo/odoo.conf \
  -u smart_construction_core --stop-after-init
```

Read-only acceptance probe:

```bash
docker exec -i \
  -e MIGRATION_ARTIFACT_ROOT=/tmp/business_fact_upgrade/20260508T_expense_fact_taxonomy \
  sc-backend-odoo-partner-acceptance-odoo-1 \
  odoo shell -d sc_partner_acceptance -c /var/lib/odoo/odoo.conf \
  < scripts/migration/business_expense_fact_taxonomy_acceptance.py
```

Result:

- status: `PASS`
- actions checked: 13
- menus checked: 22
- database writes: 0
- artifact:
  `artifacts/migration/business_fact_upgrade/20260508T_expense_fact_taxonomy/business_expense_fact_taxonomy_acceptance_v1.json`

Current acceptance data still reflects replay progress: expense contracts are
present, while many downstream payment, expense, tax, and fund facts remain
payload-backed until their write lanes are replayed into the acceptance database.
