# P3 Capability Map v0.1

Scope: reconciliation contracts for contract/settlement/payment/cost/progress.

Each capability lists code, goal, roles, models, audit points, and acceptance criteria.

## P3-CONTRACT-RECON

- Code: P3-CONTRACT-RECON
- Goal: contract totals reconcile with settlement/payment chain.
- Roles: project manager, finance manager, cost controller.
- Models: `construction.contract`, `sc.settlement.order`, `sc.settlement.order.line`, `payment.request`.
- Audit points: `contract_bound`, `contract_unbound`, `payment_submitted`, `payment_approved`, `payment_paid`.
- Acceptance:
  - Cumulative settlement uses only `sc.settlement.order.state in (approve, done)`.
  - Cumulative payment requested uses `payment.request.state in (submit, approve, approved, done)`.
  - Cumulative payment paid uses `payment.request.state == done`.
  - Reconcile delta formula is explicit and testable per contract.

## P3-PERIOD-RECON

- Code: P3-PERIOD-RECON
- Goal: locked period is the baseline for period reconciliation.
- Roles: cost controller, finance manager.
- Models: `project.cost.period`, `project.cost.ledger`, `sc.settlement.order`, `payment.request`.
- Audit points: `period_locked`, `period_unlocked`.
- Acceptance:
  - Period totals only include `project.cost.period.locked == True`.
  - Period ledger totals match sum of ledgers linked to that locked period.
  - Period payment totals only include `payment.request.state == done`.
  - Period settlement totals only include `sc.settlement.order.state in (approve, done)`.

## P3-PARTNER-RECON

- Code: P3-PARTNER-RECON
- Goal: partner-level reconciliation across contract/settlement/payment.
- Roles: finance manager, procurement lead.
- Models: `construction.contract`, `sc.settlement.order`, `payment.request`, `res.partner`.
- Audit points: `payment_submitted`, `payment_approved`, `payment_paid`.
- Acceptance:
  - Partner aggregates are computed with explicit partner_id filters.
  - Aggregates are consistent across models (same partner, same project scope).
  - Partner totals are derivable from recordsets with state filters.

## P3-AUDIT-QUERY

- Code: P3-AUDIT-QUERY
- Goal: reconciliation queries can trace back to audit events.
- Roles: audit reviewer, compliance.
- Models: `sc.audit.log`, all reconciliation chain models.
- Audit points: all P2/P3 reconciliation-related events.
- Acceptance:
  - Query dimensions include project, model/res_id, period, actor, event_code.
  - Any reconciliation delta can be mapped to event_code and source records.
  - Queries are defined as contract (no runtime implementation required).

## P3-DELTA-EXPLAIN

- Code: P3-DELTA-EXPLAIN
- Goal: provide explainable deltas for mismatch scenarios.
- Roles: finance manager, cost controller.
- Models: `construction.contract`, `sc.settlement.order`, `payment.request`.
- Audit points: `payment_submitted`, `payment_approved`, `payment_paid`.
- Acceptance:
  - Each delta uses deterministic state filters.
  - Delta explanation references record IDs and states.
  - Delta logic is testable and can be gated.

## P3-LOCKED-PERIOD-BASELINE

- Code: P3-LOCKED-PERIOD-BASELINE
- Goal: reconciliation uses locked period as authoritative baseline.
- Roles: cost controller.
- Models: `project.cost.period`, `project.cost.ledger`.
- Audit points: `period_locked`, `period_unlocked`.
- Acceptance:
  - Reconciliation ignores unlocked periods.
  - Any ledger changes after lock are blocked by P2 guard (PERIOD_LOCKED).
  - Baseline totals are reproducible in a future gate.
