# Project member placeholder screening v1

Status: PASS  
Iteration: `ITER-2026-04-14-0030S`  
Database: `sc_demo`

This batch screened project_member rows after the 0030R readonly dry-run. It
did not create users, project members, ACLs, or record rules.

## Result

| Item | Result |
| --- | ---: |
| total rows | 21390 |
| mapped projects | 21390 |
| unmapped projects | 0 |
| mapped users | 7389 |
| placeholder-user rows | 14001 |
| mapped-user safe candidates | 7389 |
| duplicate project/user pairs | 735 |
| unique no-placeholder candidates | 34 |

## Placeholder Policy

`placeholder_user` rows are write-blocked. They must not be materialized as real
project members without a separate authority decision.

Allowed next movement:

- use only no-placeholder rows;
- keep placeholder rows out of write mode;
- do not create fallback users;
- do not change record rules or ACLs in the migration write batch.
