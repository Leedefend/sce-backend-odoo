# Project Write Trial Expand Gate v1

## Decision

Expansion is BLOCKED for now.

The 30-row write trial is technically successful, but expansion requires manual
acceptance of Odoo default `stage_id` behavior and completion of rollback dry-run
planning.

## Evidence

| Check | Result |
| --- | ---: |
| sample rows written | 30 |
| records found | 30 |
| unique identities | 30 |
| missing identities | 0 |
| duplicate identities | 0 |
| empty project names | 0 |
| rows with default `stage_id` | 30 |

## Expansion Preconditions

Before expanding the create-only sample:

1. Manual review checklist must be completed.
2. `stage_id` default behavior must be explicitly accepted or handled.
3. Rollback dry-run design must be converted into a dry-run script and executed
   without deletion.
4. The 30 written records must be approved as usable skeleton data.
5. A new bounded sample size must be declared.
6. A new task contract must be created.
7. The next batch must remain create-only unless a separate update/upsert gate
   is approved.

## Expansion Refusal Rules

Do not expand if:

- any of the 30 records are missing;
- any duplicate `legacy_project_id` exists;
- any project name is empty;
- `stage_id` default behavior remains unacceptable or unexplained;
- rollback dry-run cannot precisely target only the 30 identities;
- new mappings are requested for company, specialty, lifecycle/state, user,
  partner, contract, payment, supplier, tax, bank, cost, settlement, or
  attachment data.

## Current Conclusion

The current state supports post-write review and rollback rehearsal planning.
It does not yet authorize a larger create-only sample.
