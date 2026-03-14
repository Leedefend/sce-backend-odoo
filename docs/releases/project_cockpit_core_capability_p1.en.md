# Project Cockpit Core Capability P1 (Frozen Scope)

## 1. Objective

Upgrade `project.management` from a display shell to an operational cockpit, while keeping the existing 7-block contract envelope unchanged.

P1 answers three questions:

1. Is the project healthy?
2. Which indicators are drifting?
3. What should be handled first today?

## 2. Boundaries

- Do not change scene registry / governance / delivery policy core mechanics;
- Do not change ACL baseline;
- Do not break `project.dashboard` contract envelope;
- Only add business-semantic aggregate fields under block `data`;
- Keep `verify.project.dashboard.contract` passing.

## 3. P1 Scope (7 blocks)

- Header: project identity and stage context;
- Metrics: contract/output/cost/cash/risk KPIs;
- Progress: task completion + milestone progress + delay signals;
- Contract: total/executed/change/performance rate;
- Cost: target/actual/variance/variance rate;
- Finance: receivable/received/payable/paid/gap;
- Risk: total/high-risk/risk score/risk level.

## 4. Data Strategy

- Business models first (`project.task`, `construction.contract`, `project.cost.ledger`, `payment.request`, `project.risk`);
- Missing models/fields should return safe defaults, preserving contract stability;
- Each block may expose both:
  - compatibility fields (legacy rendering);
  - semantic fields (productized rendering).

## 5. Done Criteria

- All 7 blocks provide explainable business semantics;
- Page can answer health/drift/priority;
- Existing verification chain remains intact.

## 6. Display Priority (Frontend Convergence)

Without changing the 7-block contract, the cockpit uses a fixed product order:

1. Metrics;
2. Risk + Progress;
3. Contract + Cost + Finance;
4. Header (context closure area).

This order ensures first-screen attention goes to KPI/risk/progress before detailed operating sections.

## 7. Refinement in This Iteration (P1-R2)

- Added business hints on KPI cards (for example: revenue baseline, payment/contract ratio);
- Distinguished percentage progress vs delayed counts in progress block (avoid rendering delayed counts as percentages);
- Strengthened risk-card visual priority inside risk zone for faster escalation.

## 8. Refinement in This Iteration (P1-R3)

- Compressed Header summary into identity/context essentials to reduce noise;
- Normalized Cost section into four semantic items (target/actual/variance/variance rate);
- Unified Contract and Finance table presentation (title hierarchy, row rhythm, zebra rows, section tones) for consistent operating language.
