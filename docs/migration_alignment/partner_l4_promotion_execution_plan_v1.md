# Partner L4 promotion execution plan v1

Status: READY_FOR_NEXT_BATCH
Iteration: `ITER-2026-04-14-MIG-FAST-LEDGER`

## Batch target

Promote the partner importer from validated L3 sample evidence toward an L4
repeatable-importer candidate without mixing lanes or widening semantics.

## Boundary

Allowed lane: `partner`.

Allowed target model: `res.partner`.

Allowed first write behavior: create-only for rows whose action decision is a
safe create candidate.

Forbidden behavior:

- no supplier supplement update;
- no bank account, address, contact, payment, receipt, settlement, invoice, or
  account data;
- no cross-source merge write;
- no deletion;
- no project_member, contract, or file write in the same batch.

## Step 1: partner full no-DB decision refresh

Operation:

- Run the existing partner importer in no-DB mode against the current source
  inputs.
- Emit deterministic row decisions and counters.
- Confirm that the 100 written validation rows are either recognized as existing
  validation rows or skipped by explicit idempotency rules.

Expected outputs:

- full decision summary JSON;
- row-level audit CSV;
- blocker summary;
- next safe-slice input.

Completion criteria:

- no DB writes;
- no duplicate `legacy_partner_source + legacy_partner_id`;
- all decisions are one of `create_candidate`, `skip_existing`, or `blocked`;
- no update/upsert decision appears.

## Step 2: partner slice gate

Operation:

- Freeze the next slice size from the no-DB decision output.
- Recommended acceleration sequence: `500 -> 1000 -> remaining safe candidates`.
- Start at 500 only if no-DB output proves rollback key uniqueness.

Expected outputs:

- slice CSV;
- write authorization packet;
- rollback dry-run plan;
- post-write review command list.

Completion criteria:

- every slice row has non-empty `legacy_partner_id`;
- `legacy_partner_source` is explicit;
- the slice excludes previously written validation rows unless the importer
  intentionally classifies them as `skip_existing`;
- rollback target count is expected before write.

## Step 3: bounded write and immediate review

Operation:

- Run one bounded create-only slice.
- Immediately run readonly post-write review.
- Do not start the next slice until review passes.

Expected outputs:

- write summary JSON;
- rollback target CSV;
- post-write review JSON;
- iteration report.

Completion criteria:

- created count matches the allowed slice write count;
- updated count is zero;
- rollback target rows equal created rows;
- every rollback target resolves by `legacy_partner_source + legacy_partner_id`;
- `make verify.native.business_fact.static` passes.

## Step 4: L4 candidate gate

Operation:

- After at least one accelerated slice passes, generate the L4 candidate report.
- The L4 report must prove repeatability and exact skip-existing behavior.

Completion criteria:

- no-DB rerun after write classifies written rows as skip-existing or equivalent
  idempotent non-write actions;
- no duplicate rollback identities;
- full run can be repeated without creating duplicates;
- downstream contract mapping can consume the partner identity baseline.

## Next task recommendation

Open `ITER-2026-04-14-PARTNER-L4-NODB-REFRESH` as the next executable batch.

Layer target:

- Migration Importer Promotion

Module:

- `res.partner` rebuild importer

Reason:

- Partner is the frozen next main-line lane and has reviewed L3 write evidence.
  A no-DB full decision refresh is the cheapest safe way to unlock larger
  slices without cross-lane reasoning.

## Stop conditions

- acceptance command failure;
- any partner update/upsert decision before update policy exists;
- any non-partner lane write;
- any forbidden financial or authority-domain path;
- ambiguous legacy identity;
- rollback target mismatch.
