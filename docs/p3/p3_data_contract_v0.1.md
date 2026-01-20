# P3 Reconciliation Data Contract v0.1

## 0. Scope & Non-Goals

Scope chain: contract -> settlement -> payment request -> paid (done) -> locked cost period -> progress.
Non-goals: no accounting posting, no approval workflow refactor, no mobile endpoints.

## 1. Model Mapping (Evidence Paths)

Models in scope (evidence path placeholders for later validation):
- `construction.contract` (evidence: TODO)
- `sc.settlement.order` (evidence: TODO)
- `sc.settlement.order.line` (evidence: TODO)
- `payment.request` (evidence: TODO)
- `project.cost.ledger` (evidence: TODO)
- `project.cost.period` (evidence: TODO)
- `project.progress.entry` (evidence: TODO)
- `project.task` (optional; evidence: TODO)

## 2. Authoritative Sources

### 2.1 Contract Cumulative

- `contract_amount_total`
  - Source: `construction.contract.amount_total`
  - Filter: n/a (contract record scope)
  - Write policy: derived-only

- `settlement_amount_approved_cum`
  - Source: `sc.settlement.order` aggregated by `contract_id`
  - Filter: `state in (approve, done)`
  - Write policy: derived-only

- `payment_requested_cum`
  - Source: `payment.request` aggregated by `contract_id`
  - Filter: `state in (submit, approve, approved, done)` (requested means in-flight + approved + done)
  - Write policy: derived-only

- `payment_paid_cum`
  - Source: `payment.request` aggregated by `contract_id`
  - Filter: `state == done`
  - Write policy: derived-only

- `reconcile_delta`
  - Definition: `contract_amount_total - max(settlement_amount_approved_cum, payment_paid_cum)`
  - Write policy: derived-only

### 2.2 Period Cumulative

- `period_locked_cost_total`
  - Source: `project.cost.ledger` aggregated by `period_id`
  - Filter: `project.cost.period.locked == True`
  - Write policy: derived-only

- `period_payment_paid_total`
  - Source: `payment.request` aggregated by period
  - Filter: `state == done` and `date_request in period`
  - Write policy: derived-only

- `period_settlement_approved_total`
  - Source: `sc.settlement.order` aggregated by period
  - Filter: `state in (approve, done)` and `date_settlement in period`
  - Write policy: derived-only

### 2.3 Partner Cumulative

- `partner_payment_paid_cum`
  - Source: `payment.request` aggregated by `partner_id`
  - Filter: `state == done`
  - Write policy: derived-only

- `partner_settlement_approved_cum`
  - Source: `sc.settlement.order` aggregated by `partner_id`
  - Filter: `state in (approve, done)`
  - Write policy: derived-only

- `partner_reconcile_delta`
  - Definition: `partner_settlement_approved_cum - partner_payment_paid_cum`
  - Write policy: derived-only

## 3. Derived-only Field Rules

1) All derived reconciliation fields are read-only; user/ORM write must be rejected.
2) All derived values must be computed server-side with explicit dependencies and triggers.

## 4. State Filter Policy

- Settlement cumulative: only `sc.settlement.order.state in (approve, done)`.
- Payment requested cumulative: `payment.request.state in (submit, approve, approved, done)`.
- Payment paid cumulative: only `payment.request.state == done`.
- Cost ledger cumulative: only rows in locked periods (`project.cost.period.locked == True`).

## 5. Consistency Rules (Gate-Ready)

1) `payment_paid_cum <= payment_requested_cum`.
2) `settlement_amount_approved_cum <= contract_amount_total` (exceed => warn or block per policy).
3) Locked period totals are immutable once `project.cost.period.locked == True`.
4) Settlement lines must be bound to a contract (P2 contract link guard).
5) Payment submit requires attachments (P2 payment guard).
6) All reconciliation totals must be traceable via audit events and source records.

## 6. Error / Warning Codes

- P3_RECON_SOURCE_MISSING (ERROR)
- P3_RECON_CONTRACT_MISMATCH (ERROR)
- P3_RECON_OVER_CONTRACT (WARN)
- P3_RECON_NEGATIVE_DELTA (WARN)
- P3_RECON_PERIOD_UNLOCKED (WARN)
- P3_RECON_UNBOUND_SETTLEMENT_LINE (ERROR)
- P3_RECON_PAYMENT_STATE_INVALID (ERROR)
- P3_RECON_AUDIT_MISSING (WARN)
