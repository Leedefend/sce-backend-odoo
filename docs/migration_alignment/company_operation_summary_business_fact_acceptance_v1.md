# Company Operation Summary Business Fact Acceptance v1

Status: `accepted`

Task: `ITER-2026-05-10-COMPANY-OPERATION-SUMMARY`

## Acceptance Principle

The company operation summary is a user-facing continuation report for the
legacy `公司经营情况表`.

This round accepts the report when deterministic historical operating facts are
carried into a visible company-level summary. It does not require every old
procedure-specific fine-grained field to be reinterpreted as a new-system rule
before the user can inspect the migrated facts.

## Legacy Evidence

Old report:

- legacy entry: `公司经营情况表`
- legacy procedure: `Report_GSJYQKB_BSJZ`
- usage evidence: `726` clicks, `7` users, last used `2026-04-08`
- parameters: year, start date, end date

Important old source families:

- company finance income/expense: `C_CWSFK_GSCWSR`, `C_CWSFK_GSCWZC`
- receipt facts: `C_JFHKLR`, `C_JFHKLR_CB`
- expense reimbursement: `CWGL_FYBX`, `CWGL_FYBX_CB`
- payroll: `BGGL_XZ_GZ`, `BGGL_XZ_GZ_CB`
- invoice/tax and withholding related sources

## Runtime Carrier

Acceptance database:

`sc_acceptance_audit_20260510`

Runtime model:

`sc.company.operation.summary`

User entry:

`公司经营情况表`, `action_id=821`, `menu_id=626`

The runtime summary carries:

- `收款收入`
- `公司财务收入`
- `其他流入`
- `收入合计`
- `公司财务支出`
- `费用报销`
- `应发工资`
- `实发工资`
- `其他流出`
- `支出合计`
- `销项税额`
- `进项税额`
- `预缴税额`
- `经营净额`
- source counts for receipt, expense/deposit, payroll, invoice, and account
  transaction lines

## Current Evidence

Runtime row on `sc_acceptance_audit_20260510`:

| Check | Result |
| --- | ---: |
| rows | `1` |
| company | `四川保盛建设集团有限公司` |
| income amount | `3680688471.06` |
| expense amount | `748285541.27` |
| net operation amount | `2932402929.79` |
| receipt count | `19894` |
| expense/deposit count | `36496` |
| salary line count | `3290` |
| invoice count | `28010` |
| account transaction source lines | `39707` |

The previous runtime row label `未匹配公司` was a projection issue, not a
business fact gap. The acceptance database currently has one legal company,
`四川保盛建设集团有限公司`, while many migrated projects do not yet carry
`project.company_id`. The summary view now assigns project-company-blank
historical facts to the current company for this single-company upgrade
context, preserving all amounts and counts while removing the misleading
unmatched-company label.

## Browser Acceptance

Browser acceptance on daily dev port `http://localhost:18081`:

| Check | Result |
| --- | --- |
| frontend/runtime DB | `sc_acceptance_audit_20260510` |
| login user | `wutao` / `吴涛` |
| action/menu | `action_id=821`, `menu_id=626` |
| menu entry visible and clickable | `统计分析` -> `公司经营情况表` |
| report title visible | `true` |
| company row visible | `四川保盛建设集团有限公司` |
| `收入合计` visible | `true` |
| `支出合计` visible | `true` |
| `经营净额` visible | `true` |
| amount cells use at most two decimals | `true` |
| `未匹配公司` absent | `true` |

Browser evidence:

`artifacts/company-operation-summary-browser-acceptance/20260510T130215/summary.json`

## Residual Interpretation

The report is accepted as a company-level migrated operating fact summary.
Future iterations should still compare the old procedure's year/date filtering
and fine-grained management-fee, enterprise-income-tax, surcharge, and service
fee columns. Those refinements must be handled as explicit report-field
alignment, not as blockers for carrying the already migrated operating facts.
