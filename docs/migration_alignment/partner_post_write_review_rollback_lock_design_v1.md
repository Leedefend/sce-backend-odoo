# Partner Post-Write Review And Rollback Dry-Run Lock Design v1

Iteration: `ITER-2026-04-13-1855`

## Purpose

Freeze the mandatory follow-up design for any authorized 30-row `res.partner` create-only write.

This document does not authorize write or delete execution.

## Required Immediate Sequence

If a future batch creates the locked 30-row partner sample, the next batches must run in this order:

1. post-write readonly review;
2. rollback dry-run lock;
3. manual keep-or-rollback decision;
4. real rollback only if separately authorized.

No supplier supplement, contract import, partner merge, or attachment work may run between the write batch and the post-write review.

## Post-Write Readonly Review Contract

The readonly review must verify:

- sample row count;
- created count;
- skipped count;
- duplicate legacy identity count;
- missing legacy identity count;
- out-of-scope source count;
- forbidden field write count;
- exact match between the sample and written legacy identities.

Readonly review identity is:

- `legacy_partner_source`;
- `legacy_partner_id`.

Readonly review must not use name text as the primary match key.

## Rollback Dry-Run Lock Contract

The rollback dry-run must emit a lock list with:

- run id;
- Odoo `res.partner.id`;
- `legacy_partner_source`;
- `legacy_partner_id`;
- partner name;
- `legacy_source_evidence`;
- original sample row number;
- rollback eligibility decision.

The lock list must reject any row when:

- the legacy identity resolves to zero partners;
- the legacy identity resolves to more than one partner;
- the source is not `cooperat_company`;
- the row is not part of `artifacts/migration/partner_30_row_create_only_sample_v1.csv`;
- the row was not created by the authorized sample write batch.

## Delete Boundary

Rollback dry-run is not delete authorization.

Any real delete batch must be a separate task contract with explicit authorization, exact lock-list input, and post-delete readonly verification.

## Promotion Decision

The partner importer cannot move beyond bounded-write stage until:

- post-write readonly review passes;
- rollback dry-run lock passes;
- no duplicate legacy identities are found;
- no out-of-scope partner is locked;
- the keep-or-rollback decision is recorded.
