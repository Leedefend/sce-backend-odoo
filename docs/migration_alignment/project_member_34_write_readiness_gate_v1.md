# Project member 34-row write readiness gate v1

Status: WRITE_BLOCKED  
Iteration: `ITER-2026-04-14-0030W`  
Database: `sc_demo`

## Scope

This gate reviewed the 34-row no-placeholder project_member safe slice from
`ITER-2026-04-14-0030S`.

No project_member records were created, updated, or deleted.

## Result

| Item | Result |
| --- | ---: |
| safe slice rows | 34 |
| matched project records | 34 |
| matched user records | 2 |
| placeholder rows | 0 |
| duplicate project/user pairs | 0 |
| existing target project/user pairs | 0 |
| db writes | 0 |

## Blocking Decision

The target model `project.responsibility` requires the business fact
`role_key`.

Allowed target roles are:

- `manager`
- `cost`
- `finance`
- `cashier`
- `material`
- `safety`
- `quality`
- `document`

The legacy source columns are:

```text
ID, PID, USERID, XMID, XMMC, LRR, LRRID, LRSJ
```

The no-placeholder safe slice columns are:

```text
legacy_member_id, legacy_project_id, project_id, project_name,
legacy_user_id, legacy_user_name, mapped_user_id, mapped_user_name,
user_match_mode, source_project_name
```

No legacy role column is present. Therefore assigning a fixed role such as
`document` or `manager` would fabricate a required business fact and would also
affect project visibility semantics through `project.responsibility`.

## Gate Outcome

`project_member` must not proceed to create-only L3 write until one of these is
defined in a new task:

- an authoritative legacy role source;
- a business-approved default role mapping rule;
- a separate neutral carrier for membership identity that does not require
  inventing `project.responsibility.role_key`.

Placeholder-user rows remain blocked.
