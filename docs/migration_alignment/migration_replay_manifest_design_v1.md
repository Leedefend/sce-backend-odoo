# Migration Replay Manifest Design v1

Status: PASS

Task: `ITER-2026-04-15-MIGRATION-REPLAY-MANIFEST-DATA-LAYER-POLICY`

## Decision

Completed migration data is **not yet certified as one-click replayable** in a
fresh database.

It is close: most completed lanes have scripts, task contracts, rollback
targets, aggregate reviews, and reports. Certification still requires a single
manifest and runner that can replay the lanes on a newly rebuilt database and
prove the aggregate result.

## Required Before Fresh Rebuild

The next phase must create or confirm:

- a replay manifest with lane order, dependencies, source artifacts, target
  model, legacy identity key, and expected counts;
- a runner design that executes `precheck -> write -> aggregate review ->
  residual blocker ledger`;
- lane status tags: `replayable`, `current-db-only`, `deprecated`,
  `high-risk-deferred`;
- a fresh database operation contract that names the database and declares the
  destructive boundary;
- aggregate verification after replay.

## Replay Lane Order

1. Bootstrap/schema install: not run by default in the migration runner; fresh
   database creation and module installation are a separate high-risk operation.
2. L0 partner anchors.
3. L0 project anchors.
4. L1 project-member neutral facts.
5. L1 contract headers already proven by the 1332-row lane.
6. L0 contract partner-anchor recovery for the 12 company-source anchors.
7. L1 contract retry for the 57 dependent contract rows.
8. Receipt/header lanes only after readiness screen.
9. Payment, settlement, and accounting only under dedicated high-risk task
   contracts.

## Replay Certification Standard

A lane is replay-certified only when all are true:

- source artifact and raw source file are declared;
- target model and legacy identity key are declared;
- precheck proves dependencies exist;
- write is idempotent by legacy key;
- rollback target is generated;
- aggregate review confirms source/write/target counts;
- residual blocker ledger is updated.

## Current Fresh-Database Stance

The next operational phase may rebuild a fresh database, but the first task
must be a dedicated fresh database replay-preparation task, not direct data
write. The runner should default to low-risk replayable lanes and exclude
payment, settlement, accounting, ACL, manifest, and module install steps unless
their task contracts explicitly authorize them.
