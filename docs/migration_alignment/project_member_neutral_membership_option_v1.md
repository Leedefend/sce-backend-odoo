# Project member neutral membership option v1

Status: RECOMMENDED_NEXT_DESIGN  
Iteration: `ITER-2026-04-14-0030RD`

## Decision

Neutral membership carrier:

```text
recommended, not implemented in this batch
```

Reason:

The old database confirms the relation fact but does not confirm the
responsibility role fact.

Known relation fact:

```text
project + user + legacy_member_id
```

Missing role fact:

```text
project.responsibility.role_key
```

## Boundary

A neutral membership carrier must preserve:

- member exists;
- project mapping is known;
- user mapping is known;
- legacy member identity is known;
- no responsibility role is claimed.

It must not:

- write `project.responsibility.role_key`;
- use a placeholder role;
- silently grant project visibility through existing `project_member_ids.user_id`
  record-rule domains;
- change ACL or record-rule files in the same task.

## Permission Impact

Current `project.responsibility` is not neutral because record rules already
reference:

```text
project_member_ids.user_id
project_id.project_member_ids.user_id
```

Therefore writing the 21390 rows into `project.responsibility` would change
visibility semantics even if `role_key` were assigned mechanically.

A neutral carrier should be evaluated as a separate model or staging carrier
that does not participate in record rules until a dedicated authority batch
explicitly wires it.

## Next Branch

Open:

```text
ITER-2026-04-14-0030N project_member neutral-membership carrier design
```

That task should decide the carrier shape and rollback identity before any L3
write.
