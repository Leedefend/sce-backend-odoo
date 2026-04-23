# Project member L3 role-source closure v1

Status: BLOCKED_BY_APPROVAL  
Iteration: `ITER-2026-04-14-L3-ROLE-SOURCE-CLOSURE`

## Scope

This batch closes the L3 responsibility candidate loop with an approval gate.
It does not authorize broad responsibility migration.

Allowed:

- export the L3 business review checklist;
- freeze valid role-source rules;
- dry-run exactly three sample rows;
- write only approved three-row sample records;
- audit the write result and rollback target.

Forbidden:

- expanding beyond three sample rows;
- writing pending or rejected rows;
- fabricating `role_key`;
- modifying ACL or record rules.

## Frozen Rule

`project.responsibility` write is allowed only when all conditions are true:

- `business_decision = approved`;
- `proposed_role_key` is one of `manager`, `cost`, `finance`, `cashier`,
  `material`, `safety`, `quality`, `document`;
- `role_source_evidence` is non-empty;
- `business_reviewer` is non-empty;
- the row is inside the first three L3 sample rows.

Migration authorization is not a role-source approval.

## Execution Result

The review checklist and frozen rule artifact were generated.

The three-row sample dry-run found:

- approved sample rows: 0
- blocked sample rows: 3
- write allowed: false
- database writes: 0

The apply gate ran in `sc_demo` and returned `BLOCKED_BY_APPROVAL`.

No `project.responsibility` row was created because the first three L3 sample
rows still have:

- `business_decision = pending`;
- empty `proposed_role_key`;
- empty `role_source_evidence`;
- empty `business_reviewer`.

The post-write audit therefore returned `SKIPPED_NO_WRITE`.
