# P3 Scope & Boundary v0.1

Goal: upgrade P2 "execution control + audit" to P3 "reconciliation contract" with consistent metrics, queryability, and traceability.

## Scope (Reconciliation Chain)

Covered models:
- Contract: `construction.contract`
- Settlement: `sc.settlement.order`, `sc.settlement.order.line`
- Payment Request: `payment.request`
- Cost Ledger: `project.cost.ledger`, `project.cost.period`
- Progress: `project.progress.entry`

## Reconciliation Perspectives

1) Contract view
- Compare contract amount vs cumulative settlement approved vs cumulative payment requested vs cumulative payment paid.

2) Period view
- Compare locked-period cost ledger totals vs settlement/payment movement in the same period.

3) Partner (vendor/customer) view
- Aggregate contract/settlement/payment totals by partner for cross-chain reconciliation.

## Boundaries (Out of Scope)

- No accounting posting or journal entries.
- No approval workflow refactor (keep tier + existing state machines).
- No mobile endpoints or mobile UI changes.

## Deliverable Assertions (v0.1)

- Derived reconciliation fields are read-only and sourced from authoritative models/states.
- Reconciliation queries can be answered using audit logs plus model-state filters.
- Period-lock rules from P2 are used as reconciliation baselines.

## Acceptance (Gate-Ready)

- All derived fields are read-only and computed from explicit sources and state filters.
- Contract view, period view, partner view each has a deterministic formula and testable inputs.
- Any reconciliation delta can be traced to a chain of records with model/state filters.
- No changes to approval workflows, accounting postings, or mobile flows.
