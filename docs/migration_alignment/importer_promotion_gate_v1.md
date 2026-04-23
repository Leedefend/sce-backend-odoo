# Importer promotion gate v1

Status: FROZEN  
Iteration: `ITER-2026-04-14-0027`

Every migration lane must move through the same five promotion levels before it
can write to a formal rebuild database.

## Promotion Levels

| Level | Name | Meaning | Write scope | Exit evidence |
| --- | --- | --- | --- | --- |
| L0 | probe | Read inputs and learn source shape | No DB write | source inventory, field candidates, unknowns |
| L1 | dry-run | Build deterministic mapping and conflict accounting | No DB write | JSON result, missing fields, conflicts, dedup/merge plan |
| L2 | safe-slice | Freeze a small clean slice | No DB write unless separately authorized | slice CSV, zero known conflicts, rollback plan |
| L3 | bounded-write | Execute an authorized controlled validation write | `sc_demo` only | write result JSON, post-write review, rollback targets |
| L4 | repeatable-importer | Promote to rebuild-grade importer | formal rebuild database eligible | deterministic pipeline, idempotency rules, verification report |

## Hard Rules

- No importer below L4 may write to `future_prod_db`.
- L3 writes are validation writes and must remain bounded to the active lane.
- Every write batch must generate rollback targets.
- A lane may not skip L1 dry-run conflict accounting.
- A lane may not skip L2 safe-slice selection before L3.
- Each lane owns its own promotion evidence; evidence from another lane cannot
  promote it.

## Required Dry-Run Result Shape

Dry-run JSON must include at least:

```json
{
  "total": 0,
  "deduplicated": 0,
  "to_create": 0,
  "to_merge": 0,
  "missing_fields": [],
  "conflicts": []
}
```

Lane-specific fields may be added, but these keys must remain stable.

## Write Authorization Boundary

Authorization is scoped to:

- one lane
- one environment
- one slice
- one write mode
- one rollback target strategy

Any change to those dimensions requires a new task line.
