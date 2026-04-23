# Partner Supplier Supplement Screening v1

Iteration: `ITER-2026-04-13-1856`

## Scope

This is a screen-only batch based on existing artifacts from `ITER-2026-04-13-1842` and `ITER-2026-04-13-1843`.

No raw files are rescanned. No partner records are created.

## Existing Evidence

From `partner_source_inventory_v1`:

- company source rows: 7864;
- supplier source rows: 3041;
- company distinct normalized names: 7046;
- supplier distinct normalized names: 2953;
- both sources contain duplicate names.

From `partner_candidate_confirmation_summary_v1`:

- counterparty texts: 568;
- `company_single`: 419;
- `company_multiple`: 78;
- `cross_source_conflict`: 8;
- `defer`: 63.

## Screening Decision

Supplier source is a supplemental role source, not a primary create stream for the current partner rebuild line.

Supplier rows may only enter later batches as:

- supplemental attributes for a partner already created or locked from company primary source;
- conflict evidence for `cross_source_conflict`;
- manual review evidence for supplier-specific role enrichment.

Supplier rows must not:

- create standalone partners before company primary-source sample write is validated;
- overwrite company primary identity;
- resolve `company_multiple` by name text alone;
- backfill contract counterparties directly;
- write bank, payment, settlement, invoice, receipt, or account facts.

## Next Allowed No-DB Step

The next no-DB step may prepare a supplier supplement design only after it declares:

- company primary identity remains authoritative for the current partner write line;
- supplier identity must be mapped as supplemental source evidence;
- cross-source conflicts require manual decision;
- no supplier supplement write occurs before the 30-row partner primary sample has passed post-write review and rollback dry-run lock.

## Stop Boundary

If the next batch needs to create partners, update partners, or attach supplier attributes to real records, it must become a dedicated write-capable task and require explicit authorization.
