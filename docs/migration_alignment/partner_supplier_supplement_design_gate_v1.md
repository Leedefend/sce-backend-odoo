# Partner Supplier Supplement Design Gate v1

Iteration: `ITER-2026-04-13-1857`

## Decision

Supplier supplement remains `NO-GO` for writes.

Supplier-origin facts may become an enrichment line only after the company-primary 30-row partner sample has passed:

1. authorized create-only write;
2. post-write readonly review;
3. rollback dry-run lock;
4. keep-or-rollback decision.

## Design Boundary

Supplier supplement may later provide:

- supplier role evidence;
- supplier source identity;
- qualification evidence;
- supplier classification evidence;
- manual conflict context.

Supplier supplement must not provide:

- primary `res.partner` creation identity for the current line;
- contract counterparty backfill;
- bank data;
- payment, receipt, settlement, invoice, or account facts;
- automatic merge decisions;
- updates to existing company-primary partners without a dedicated update gate.

## Identity Rule

The current primary partner identity remains:

- `legacy_partner_source = cooperat_company`;
- `legacy_partner_id = T_Base_CooperatCompany.Id`.

Supplier identity, when introduced later, must be stored or mapped as supplemental evidence and must not overwrite the primary identity.

## Later Gate Requirements

A future supplier supplement batch must define:

- exact supplier source identity fields;
- whether the target partner was created by the company-primary line;
- conflict handling for the 8 `cross_source_conflict` candidate texts;
- skip rules for ambiguous supplier names;
- rollback strategy for any supplemental update;
- explicit write authorization if any `res.partner` field is updated.

## Current Result

This batch only freezes the design gate. It does not create partners, update partners, or attach supplier attributes.
