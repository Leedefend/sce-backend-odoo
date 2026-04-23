# Project member role fact decision v1

Status: FROZEN  
Iteration: `ITER-2026-04-14-0030RF`  
Decision source: `ITER-2026-04-14-0030W`, `ITER-2026-04-14-0030RD`, `ITER-2026-04-14-0030N`

## Formal Decision

`ITER-2026-04-14-0030W` is the formal stop gate for direct
`project.responsibility` writes.

The frozen route is:

```text
Do not write project.responsibility.
Do not assign a default role_key.
Do not change record rules.
Preserve membership facts in the neutral carrier.
Keep role-fact sourcing and responsibility promotion in a separate decision path.
```

## Why 0030W Stops The Direct Write

The 34-row safe slice passed the relation-level checks:

- project matched: 34;
- user matched: 2 distinct users;
- placeholder rows: 0;
- duplicate project/user pairs: 0;
- existing target project/user pair conflicts: 0;
- database writes: 0.

The only blocker was:

```text
required_role_fact_missing
```

This means the data quality problem is not the member relation. The missing
fact is the responsibility role required by `project.responsibility.role_key`.

## Question 1: Is There An Authoritative Legacy Role Source?

Answer:

```text
No.
```

Evidence:

- `dbo.BASE_SYSTEM_PROJECT_USER` has 21390 rows and no role-like columns.
- Direct old-database probing found 454 role-like columns elsewhere.
- 17 project/user/role candidate tables were checked by shape.
- Best mapping coverage back to `BASE_SYSTEM_PROJECT_USER` was `0.0`.

Conclusion:

No current source can map `legacy_member_id + XMID + USERID` to a verified
target `role_key`.

## Question 2: Is A Business-Approved Default Role Allowed?

Answer:

```text
No.
```

No risk acceptor or business rule has approved assigning `manager`, `cost`,
`finance`, `cashier`, `material`, `safety`, `quality`, or `document` as a
default role.

Inventing a role would create unverifiable responsibility facts and could pollute
project and downstream document visibility through the existing responsibility
chain.

## Question 3: What Happens To The Member Facts?

Answer:

```text
Keep them in sc.project.member.staging.
```

`ITER-2026-04-14-0030N` implemented the neutral carrier and wrote the original
34 safe-slice rows. Later neutral expansion batches may continue to preserve
legacy membership evidence, but the carrier remains outside responsibility,
permission, approval, owner, and workflow semantics.

## Promotion Decision

Current promotion decision:

```text
Do not promote neutral carrier rows to project.responsibility.
```

Promotion may be reopened only by a separate task after one of these becomes
true:

- a verified legacy role source is found;
- a business-approved default responsibility rule is documented with a risk
  acceptor;
- a dedicated authority-path batch explicitly accepts record-rule and visibility
  impact.
