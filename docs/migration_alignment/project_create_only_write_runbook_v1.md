# Project Create-Only Write Runbook v1

## Purpose

This runbook defines the later write batch shape. It does not execute the write
batch and does not implement an importer in this iteration.

## Batch Scope

- Target model: `project.project`
- Target database: `sc_demo`
- Input: `data/migration_samples/project_sample_v1.csv`
- Row count: 30
- Mode: create-only
- Identity key: `legacy_project_id`
- Update mode: forbidden

## Required Steps For The Later Write Batch

1. Create a new high-risk task contract for the write batch.
2. Re-run preflight: `pwd`, repo root, branch, and limited status.
3. Re-export target identity snapshot from `sc_demo`.
4. Re-run dry-run with the target identity snapshot.
5. Require `create=30`, `update=0`, `error=0`.
6. Create a pre-write backup or snapshot of `project.project` identity state.
7. Execute the create-only importer in an explicit write mode.
8. Write only the approved 22 safe-slice fields.
9. Emit a row-level create result artifact.
10. Re-export target identity snapshot after write.
11. Verify exactly 30 new `legacy_project_id` values exist.
12. Run the required Makefile verification gate.

## Write Transaction Rule

The later importer should treat the 30-row sample as one controlled batch. If
any row fails validation before write, the importer must reject the whole batch.

If runtime write errors occur after writes begin, the batch must stop and follow
the rollback plan in `project_create_only_write_rollback_v1.md`.

## Required Pre-Write Rejections

Reject the batch before any write if:

- the CSV has more or fewer than 30 rows;
- the CSV contains fields outside the approved safe-slice set;
- any row lacks `legacy_project_id`;
- any row lacks `name`;
- duplicate `legacy_project_id` exists;
- target identity snapshot contains any matching `legacy_project_id`;
- target dry-run produces update rows;
- target dry-run produces error rows.

## Required Post-Write Checks

After a later approved write batch, check:

- 30 project records with the sample `legacy_project_id` values exist;
- no duplicate `legacy_project_id` values exist;
- no unsafe relation fields were written by the importer;
- no contract/payment/supplier/attachment rows were created;
- the row-level result artifact matches the 30 input rows;
- `make verify.native.business_fact.static` passes.

## Explicit Non-Scope

Do not handle:

- upsert or update;
- company mapping;
- specialty mapping;
- lifecycle/stage/state writes;
- user or partner matching;
- contract, payment, supplier, tax, bank, cost, settlement, or attachment import;
- menu, view, frontend, ACL, record rule, or manifest changes.
