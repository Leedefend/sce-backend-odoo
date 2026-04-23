# Full Rebuild Importer Promotion Standard v1

Iteration: `ITER-2026-04-13-1853`

## Purpose

Freeze the minimum standard for promoting any migration script into the repeatable full new-database rebuild pipeline.

This standard exists because a probe that runs once is not a production rebuild importer.

## Required Promotion Ladder

Every importer must move through these stages:

1. `probe`: read source facts and produce evidence.
2. `mapping-dry-run`: classify source-to-target mapping without writes.
3. `safe-slice`: freeze the allowed field set and forbidden field set.
4. `no-db-importer`: produce deterministic row decisions and summary artifacts without database writes.
5. `write-mode-gate`: freeze idempotency, rollback, sample size, and post-write review rules.
6. `bounded-write`: create or update only the explicitly authorized sample.
7. `post-write-review`: verify readability, counts, identity locks, and side effects.
8. `rollback-dry-run`: prove exact rollback target selection.
9. `repeatable-importer`: only after bounded write and rollback dry-run pass.

Skipping stages is forbidden.

## Eight Mandatory Importer Capabilities

Each importer must provide:

1. `no-DB mode`
   - It can run analysis/dry-run without writing the database.

2. `slice mode`
   - It can run a bounded subset such as 10, 30, 50, or 100 rows.

3. `idempotent strategy`
   - It explicitly declares `create-only`, `skip-existing`, `update-only`, or `upsert`.

4. `legacy identity`
   - It has a stable old-system key mapped into the new system.

5. `rebuild log`
   - It emits run id, row-level decisions, counters, and blocker reasons.

6. `rollback strategy`
   - It can lock the exact objects written by a batch.

7. `verification step`
   - It defines post-write readonly checks and machine-readable verification outputs.

8. `promotion gate`
   - It declares what evidence allows the importer to move to the next stage.

## Minimum Output Contract

Every no-DB or write-capable importer must emit:

- run id;
- input path;
- input row count;
- output row count;
- action counts;
- blocker counts;
- row-level audit path;
- summary JSON path;
- decision;
- next step.

## Identity Rule

Name text is never a primary rebuild identity.

The primary identity must be a stable legacy key, such as:

- `legacy_partner_source + legacy_partner_id`;
- `legacy_project_id`;
- `legacy_contract_id`;
- legacy file id plus relation key.

Text fields may be used only for review, reporting, or auxiliary matching.

## Write-Mode Rule

Write mode requires a dedicated task contract and explicit authorization when it creates, updates, deletes, or links business records.

First write batches should default to `create-only` unless a prior gate proves update/upsert safety.

## Rollback Rule

Rollback must be keyed by the same legacy identity used for idempotency.

Rollback by name, company text, contract text, or amount is forbidden.

## Promotion Blockers

An importer cannot be promoted if any of the following are true:

- no stable legacy identity exists;
- no row-level audit exists;
- no no-DB mode exists;
- write behavior is not idempotent;
- rollback target cannot be precisely locked;
- mapping depends on ambiguous name text;
- post-write readonly verification is undefined;
- the importer touches payment, settlement, account, ACL, manifest, or security domains without a dedicated high-risk task line.

## Current Reference Implementation

The current reference candidate is the partner rebuild chain:

- `ITER-2026-04-13-1846`: partner strong-evidence dry-run input;
- `ITER-2026-04-13-1848`: no-DB partner dry-run;
- `ITER-2026-04-13-1849`: partner legacy identity field alignment;
- `ITER-2026-04-13-1851`: no-DB rebuild importer shape;
- `ITER-2026-04-13-1852`: write-mode gate and rollback policy.

It is not yet a repeatable production importer because bounded write and rollback dry-run have not run.
