# Partner 30-Row Write Authorization Packet v1

Iteration: `ITER-2026-04-13-1854`

## Decision

The first partner write sample is locked, but write mode remains `NO-GO`.

This packet prepares the next batch. It does not authorize this batch to create `res.partner` rows.

## Locked Sample

Sample file:

- `artifacts/migration/partner_30_row_create_only_sample_v1.csv`

Selection rule:

- source file: `artifacts/migration/partner_rebuild_importer_rows_v1.csv`;
- first 30 rows whose `dry_run_action` is `create_candidate`;
- source is `T_Base_CooperatCompany`;
- `legacy_partner_id` is non-empty.

Locked counts:

- sample rows: 30;
- source: `T_Base_CooperatCompany`;
- dry-run action: `create_candidate`;
- database writes in this batch: 0.

## Allowed Next Write Behavior

The next write-capable batch may only use create-only mode.

Allowed write fields remain:

- `name`;
- `company_type`;
- `legacy_partner_id`;
- `legacy_partner_source`;
- `legacy_partner_name`;
- `legacy_credit_code`;
- `legacy_tax_no`;
- `legacy_deleted_flag`;
- `legacy_source_evidence`.

The idempotency key remains:

- `legacy_partner_source`;
- `legacy_partner_id`.

## Forbidden Next Write Behavior

The next write-capable batch must not write:

- supplier supplement fields;
- bank accounts;
- addresses;
- contacts;
- contract partner links;
- payment, settlement, invoice, receipt, or account data;
- deleted legacy partners;
- cross-source merge decisions;
- any update/upsert behavior.

## Required Explicit Authorization

Before the next batch creates real partners, the user must explicitly authorize a write batch for:

- model: `res.partner`;
- sample: `artifacts/migration/partner_30_row_create_only_sample_v1.csv`;
- mode: `create-only`;
- row count: 30;
- database: declared by the write batch;
- immediate next batch: post-write readonly review and rollback dry-run lock.

General continuation wording is not treated as authorization for real `res.partner` creation.

## Next Batch Gate

The next task contract must include:

- the exact sample path;
- the exact write script path;
- write mode fixed to `create-only`;
- a post-write lock artifact keyed by `legacy_partner_source + legacy_partner_id`;
- immediate post-write readonly review;
- immediate rollback dry-run lock.
