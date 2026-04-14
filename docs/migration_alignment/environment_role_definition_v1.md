# Environment role definition v1

Status: FROZEN  
Iteration: `ITER-2026-04-14-0027`

This document defines the database roles for the migration program after the
project lane reached `BASELINE_READY_FOR_DOWNSTREAM_MAPPING`.

## Roles

| Environment | Role | Allowed use | Forbidden use |
| --- | --- | --- | --- |
| `sc_demo` | Migration validation database | Probe, dry-run verification, authorized safe-slice writes, authorized rollback checks, repeatability validation | Treating validation writes as production promotion, mixing lanes in one write batch |
| `future_prod_db` | Formal rebuild database | Install and run only L4 repeatable importers in the frozen lane order | Probe scripts, ad hoc writes, manual patch imports, non-repeatable corrections |

## Rules

- The current `sc_demo` database is not the final production rebuild target.
- `sc_demo` remains the place to validate rules, rollback behavior, and
  importer repeatability.
- `future_prod_db` is written only by mature pipelines that have reached L4.
- A successful `sc_demo` bounded write proves a lane rule; it does not promote
  that script into the formal rebuild pipeline by itself.
- Any production-like rebuild must start from a new database and follow the
  frozen lane order.

## Promotion boundary

An importer may enter `future_prod_db` only after it satisfies:

- deterministic input mapping
- dry-run output with conflict accounting
- safe-slice write validation
- rollback target generation for validation writes
- repeatable execution contract and report

Until then, all importer work remains in `sc_demo`.
