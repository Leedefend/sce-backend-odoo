# Partner Cross-Source Conflict Classification v1

Iteration: `ITER-2026-04-13-1858`

## Scope

This batch classifies the 8 `cross_source_conflict` partner candidates from the existing confirmation table.

It does not decide final source ownership and does not create or update partners.

## Input

- Source table: `artifacts/migration/partner_candidate_confirmation_v1.csv`
- Output slice: `artifacts/migration/partner_cross_source_conflicts_v1.csv`

## Conflict Counts

- conflict texts: 8;
- total contract rows covered: 123;
- all rows require manual source confirmation;
- all rows remain `auto_create_allowed = no`.

## Classification

These rows are source conflicts because the same counterparty text has both company and supplier evidence, or competing source candidates.

Classification result:

- `company_candidate_count = 1` and `supplier_candidate_count = 1`: 5 rows;
- `company_candidate_count = 3` and `supplier_candidate_count = 1`: 3 rows;
- final source decision: not made in this batch.

## Handling Rule

No automatic source winner is allowed.

For each row, a later manual decision must record:

- selected source;
- selected legacy source id;
- reason for rejecting the other source;
- whether the losing source becomes supplemental evidence;
- whether the row is eligible for partner create/update after the company-primary sample is reviewed.

## Stop Boundary

Any final source decision, partner write, supplier supplement update, or contract backfill must be a later dedicated task with explicit scope.
