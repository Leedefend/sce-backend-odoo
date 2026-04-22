# Legacy Expense Deposit Fact Screen v1

Status: `PASS`

This is a read-only screen for expense, financial outflow, and deposit-related legacy facts.

## Result

- raw rows: `14330`
- loadable rows: `11167`
- blocked rows: `3163`
- DB writes: `0`
- Odoo shell: `false`

## Source table readiness

| Source table | Raw rows | Loadable candidates |
|---|---:|---:|
| ZJGL_BZJGL_Pay_FBZJ | 3111 | 2871 |
| C_CWSFK_GSCWZC | 2726 | 2656 |
| ZJGL_BZJGL_Pay_FBZJTH | 1959 | 1872 |
| CWGL_FYBX | 1866 | 1432 |
| ZJGL_BZJGL_Branch_SBZJDJ | 1707 | 1531 |
| T_KK_SJTHB | 1206 | 0 |
| ZJGL_BZJGL_Branch_SBZJTH | 921 | 805 |
| C_JFHKLR_TH_ZCDF | 834 | 0 |

## Blocked Reasons

| Reason | Rows |
|---|---:|
| amount_not_positive_or_missing | 2504 |
| deleted | 381 |
| project_not_assetized | 343 |
| missing_project_id | 3 |

## Family Counts

| Family | Rows |
|---|---:|
| pay_guarantee_deposit | 3111 |
| company_financial_outflow | 2726 |
| pay_guarantee_deposit_refund | 1959 |
| expense_reimbursement | 1866 |
| received_guarantee_deposit_register | 1707 |
| project_deduction_refund | 1206 |
| received_guarantee_deposit_refund | 921 |
| self_funded_income_refund | 834 |

## Next lane recommendation

- lane: `legacy_expense_deposit_fact_carrier`
- source table priority: `ZJGL_BZJGL_Pay_FBZJ`
- loadable rows: `2871`
- reason: screen found project-anchored positive-amount expense/deposit facts; design a neutral carrier before XML generation

## Boundary

These rows are financial-adjacent business facts, not accounting entries.
A later carrier must not create `account.move`, settlement facts, or approval runtime facts.
