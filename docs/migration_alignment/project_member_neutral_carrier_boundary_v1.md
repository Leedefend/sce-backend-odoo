# Project member neutral carrier boundary v1

Status: FROZEN  
Iteration: `ITER-2026-04-14-0030RF`

## Carrier

```text
sc.project.member.staging
```

## Purpose

Preserve historical evidence that a legacy user belonged to a legacy project.

## Allowed Semantics

- legacy member identity;
- legacy project identity;
- legacy user identity;
- mapped project;
- mapped user;
- role fact status;
- migration evidence;
- import batch;
- rollback targeting.

## Forbidden Semantics

The carrier must not represent or drive:

- `project.responsibility`;
- `role_key`;
- record-rule visibility;
- downstream document visibility;
- approval responsibility;
- owner or reviewer responsibility;
- workflow routing;
- business authorization.

## Write Policy

Neutral carrier writes are allowed only through bounded migration tasks with:

- explicit import batch;
- rollback target list;
- `role_fact_status = missing` unless a later role-source task verifies otherwise;
- no `project.responsibility` write;
- no ACL or record-rule change.

## Promotion Policy

Promotion to `project.responsibility` is blocked until
`project_member_responsibility_promotion_rule_v1.md` is satisfied.
