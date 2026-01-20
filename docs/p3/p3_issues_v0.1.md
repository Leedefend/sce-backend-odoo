# P3 Implementation Issues v0.1

Scope: reconciliation contracts to runtime implementation backlog.

## Issues

### 1) Contract Reconciliation Summary

- Code: P3-RECON-001
- Scope: add contract-level reconciliation summary fields.
- Acceptance:
  - contract_amount_total uses contract amount_total only.
  - settlement_amount_approved_cum uses settlement approve/done only.
  - payment_paid_cum uses payment done only.
- Models: construction.contract, sc.settlement.order, payment.request
- Paths: addons/smart_construction_core/models/core/contract_center.py
- Suggested Commit: feat(p3-recon): add contract reconciliation summary fields

### 2) Contract Reconcile Delta

- Code: P3-RECON-002
- Scope: compute reconcile_delta per contract.
- Acceptance:
  - reconcile_delta = contract_amount_total - max(settlement_amount_approved_cum, payment_paid_cum).
  - delta is derived-only and not writable.
  - delta is reproducible from sources.
- Models: construction.contract
- Paths: addons/smart_construction_core/models/core/contract_center.py
- Suggested Commit: feat(p3-recon): add contract reconcile delta

### 3) Period Reconciliation Summary

- Code: P3-RECON-003
- Scope: add period-level reconciliation totals for locked periods.
- Acceptance:
  - period_locked_cost_total only aggregates locked periods.
  - period_settlement_approved_total uses settlement approve/done.
  - period_payment_paid_total uses payment done.
- Models: project.cost.period, project.cost.ledger, sc.settlement.order, payment.request
- Paths: addons/smart_construction_core/models/core/cost_period.py
- Suggested Commit: feat(p3-recon): add period reconciliation totals

### 4) Partner Reconciliation Summary

- Code: P3-RECON-004
- Scope: aggregate partner-level settlement and payment totals.
- Acceptance:
  - partner_settlement_approved_cum uses settlement approve/done.
  - partner_payment_paid_cum uses payment done.
  - partner aggregates align with record-level sums.
- Models: res.partner, sc.settlement.order, payment.request
- Paths: addons/smart_construction_core/models/core/settlement_order.py
- Suggested Commit: feat(p3-recon): add partner reconciliation aggregates

### 5) Partner Reconcile Delta

- Code: P3-RECON-005
- Scope: compute partner_reconcile_delta for partner rollups.
- Acceptance:
  - delta = partner_settlement_approved_cum - partner_payment_paid_cum.
  - derived-only, read-only.
  - negative delta raises warning.
- Models: res.partner
- Paths: addons/smart_construction_core/models/core/settlement_order.py
- Suggested Commit: feat(p3-recon): add partner reconcile delta

### 6) Audit Query Filters

- Code: P3-AUDIT-001
- Scope: implement audit query filters (project/target/event/actor/time/trace).
- Acceptance:
  - supports filters by project_id, model+res_id, event_code.
  - supports actor_uid/actor_login and time window.
  - supports trace_id correlation.
- Models: sc.audit.log
- Paths: addons/smart_construction_core/models/support/audit_log.py
- Suggested Commit: feat(p3-audit): add audit query filters

### 7) Event Code Dictionary Validation

- Code: P3-AUDIT-002
- Scope: validate event codes against dictionary.
- Acceptance:
  - unknown event_code raises warn.
  - dictionary includes P2/P3 event codes.
  - dictionary check can run in gate.
- Models: sc.audit.log
- Paths: addons/smart_construction_core/models/support/audit_log.py
- Suggested Commit: feat(p3-audit): add event code dictionary validation

### 8) Consistency Warnings for Over-Contract

- Code: P3-CONS-001
- Scope: warn when settlement_amount_approved_cum > contract_amount_total.
- Acceptance:
  - detection based on approved/done settlements only.
  - warn code P3_RECON_OVER_CONTRACT.
  - report includes contract id.
- Models: construction.contract, sc.settlement.order
- Paths: addons/smart_construction_core/models/core/contract_center.py
- Suggested Commit: feat(p3-consistency): add over-contract warning

### 9) Consistency Warnings for Negative Delta

- Code: P3-CONS-002
- Scope: warn on negative reconcile_delta.
- Acceptance:
  - delta computed from authoritative sources only.
  - warn code P3_RECON_NEGATIVE_DELTA.
  - report includes contract id.
- Models: construction.contract
- Paths: addons/smart_construction_core/models/core/contract_center.py
- Suggested Commit: feat(p3-consistency): add negative delta warning

### 10) Settlement Audit Gap Fill

- Code: P3-AUDIT-003
- Scope: add settlement submit/approve/done audit events.
- Acceptance:
  - settlement action writes event_code for submit/approve/done.
  - event records include project_id/company_id.
  - gate verifies event codes present.
- Models: sc.settlement.order
- Paths: addons/smart_construction_core/models/core/settlement_order.py
- Suggested Commit: feat(p3-audit): add settlement audit events

### 11) P3 Runtime Smoke Placeholder

- Code: P3-GATE-001
- Scope: add p3 smoke script entrypoint.
- Acceptance:
  - script runs with no side effects outside test DB.
  - validates at least one reconciliation summary and audit query.
  - outputs PASS/FAIL with exit code.
- Models: n/a
- Paths: scripts/ops/p3_runtime_smoke.py, scripts/ops/validate_p3_runtime.sh
- Suggested Commit: feat(p3-gate): add p3 runtime smoke placeholder

### 12) P3 Gate SQL Checklist

- Code: P3-GATE-002
- Scope: add SQL/static checks for reconciliation consistency.
- Acceptance:
  - SQL checks use approved/done filters only.
  - results list offending record ids.
  - can be executed in CI gate.
- Models: construction.contract, sc.settlement.order, payment.request
- Paths: scripts/ops/p3_gate_checks.sql
- Suggested Commit: feat(p3-gate): add p3 gate sql checklist

## P3 Runtime Milestones

- Sprint-R1 (minimum viable): reconciliation summary fields + minimal audit query filters + smoke baseline.
- Sprint-R2 (enhanced): full consistency rules + settlement audit gap fill.
- Sprint-R3 (engineering): p3.smoke + p3.gate scripts + CI integration.
