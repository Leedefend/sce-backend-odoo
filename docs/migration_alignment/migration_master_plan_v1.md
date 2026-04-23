# Migration master plan v1

Status: FROZEN  
Iteration: `ITER-2026-04-14-0027`

This plan upgrades the migration program from continuous validation batches to
a controlled importer promotion system.

## Current Baseline

- Current database: `sc_demo`
- Current database role: migration rule validation database
- Future formal rebuild database: `future_prod_db`
- Project lane status: `BASELINE_READY_FOR_DOWNSTREAM_MAPPING`
- Project rows materialized and post-write reviewed in `sc_demo`: 755
- Next migration main line: `partner -> project_member -> contract`

## Strategy

The migration program must not treat `sc_demo` as the final production state.
`sc_demo` is used to validate rules, safe slices, rollback behavior, and
repeatability. The formal target must be a new database rebuilt through mature
L4 importers in the frozen lane order.

## Non-Negotiable Principles

- Do not rebuild the current validation database in place.
- Advance one lane at a time.
- Do not mix model writes in one batch.
- Promote every importer through L0 to L4.
- Generate rollback targets for every validation write.
- Perform the final rebuild in a new database, not by upgrading the current
  validation database.

## Lane Order

```text
P0: project (completed)
P1: partner
P2: project_member (permission-sensitive)
P3: contract (currently NO-GO -> dry-run)
P4: receipt
P5: payment / settlement
P6: file index
P7: file binary
```

## Importer Promotion Levels

```text
L0: probe
L1: dry-run
L2: safe-slice
L3: bounded-write
L4: repeatable-importer
```

No lane may write to `future_prod_db` before reaching L4.

## Project Lane Freeze

```text
status = BASELINE_READY_FOR_DOWNSTREAM_MAPPING
rules:
- no more sample expansion
- no mixed-model write with other lanes
- only authorized correction batches may change project migration facts
```

## Next Execution Line

The next execution line is partner L1 dry-run:

- define unified partner identity
- reconcile primary partner source and supplier source
- compute duplicate groups
- produce merge strategy
- generate a clean safe slice
- keep DB writes at zero

`project_member` and `contract` must not start writes until the partner lane
provides a stable mapping baseline.
