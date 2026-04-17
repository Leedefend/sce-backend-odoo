# Legacy Settlement Fact Existence Screen v1

## Purpose

Before replaying settlement facts, this screen verifies whether imported old
business data already contains settlement-order facts or settlement-equivalent
amount facts.

The decision rule is:

- if old settlement facts exist, supplement the new-system settlement carrier
- if old settlement facts do not exist, open a new-system business-logic
  adjustment line

The screen used read-only database queries only.

## Settlement Entity Facts

Settlement-like physical tables exist, but all are empty:

- `project_settlement`: 0
- `project_settlement_line`: 0
- `sc_settlement_order`: 0
- `sc_settlement_order_line`: 0
- `sc_settlement_order_purchase_rel`: 0

No `sc.legacy.*` model carries settlement facts:

- `sc.legacy.expense.deposit.fact`: 11167, no settlement-like fields
- `sc.legacy.financing.loan.fact`: 318, no settlement-like fields
- `sc.legacy.fund.daily.snapshot.fact`: 496, no settlement-like fields
- `sc.legacy.invoice.tax.fact`: 5920, no settlement-like fields
- `sc.legacy.receipt.income.fact`: 7220, no settlement-like fields
- `sc.legacy.workflow.audit`: 79702, no settlement-like fields

## Settlement Amount Facts

Settlement-like amount fields exist on current projected tables, but all values
are zero:

- `project_project.pay_settlement_total`
  - total projects: 756
  - nonzero count: 0
  - sum: 0.0
- `sc_operating_metrics_project.settlement_amount_total`
  - total projects: 756
  - nonzero count: 0
  - sum: 0.0
- `sc_operating_metrics_project.settlement_amount_paid`
  - nonzero count: 0
  - sum: 0.0
- `sc_operating_metrics_project.settlement_amount_payable`
  - nonzero count: 0
  - sum: 0.0
- `payment_request.settlement_amount_total`
  - total requests: 30102
  - nonzero count: 0
  - sum: 0.0
- `payment_request.settlement_paid_amount`
  - nonzero count: 0
  - sum: 0.0
- `payment_request.settlement_remaining_amount`
  - nonzero count: 0
  - sum: 0.0
- `payment_request.settlement_amount_payable`
  - nonzero count: 0
  - sum: 0.0

## Existing Downstream Facts

The old imported data does contain downstream payment and ledger facts:

- `payment_request`: 30102
- `payment_ledger`: 12194

From the prior compliance screen:

- 12194 payment requests are `done` and have ledger evidence
- 17908 payment requests are `draft` and have no ledger evidence
- all 30102 payment requests currently miss `settlement_id`

## Classification

Old business data does not contain settlement-order facts or nonzero settlement
amount facts that can be directly supplemented into `sc.settlement.order`.

The available old facts are payment/ledger facts, not settlement facts.

This means the next step should not be a blind settlement replay from old
settlement data. There is no old settlement source-of-truth to replay.

## Decision

Proceed to a dedicated new-system business-logic adjustment screen.

The screen should decide how the new system should handle historical
payment/ledger facts when no old settlement facts exist, for example:

- allow completed ledger-backed historical payment facts to satisfy legacy
  compliance without requiring reconstructed settlement orders
- scope three-way validation so old orphan payments do not block new settlement
  submit/approve
- create an explicit historical-carrier policy instead of fabricating settlement
  orders without source settlement facts

No model or validation logic was changed in this screen.
