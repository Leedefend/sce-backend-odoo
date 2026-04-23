# Partner Write-Mode Gate v1

Iteration: `ITER-2026-04-13-1852`

## Decision

Current partner write mode remains `NO-GO`.

The next write-capable batch may be opened only as a dedicated, explicitly authorized small-sample create-only batch.

## Input Facts

From `ITER-2026-04-13-1851`:

- no-DB importer status: `PASS`
- input rows: 369
- output audit rows: 369
- `create_candidate`: 369
- blockers: 0

From `ITER-2026-04-13-1849`:

- `legacy_partner_id` exists on `res.partner`.
- `legacy_partner_source` exists on `res.partner`.
- `legacy_partner_name` exists on `res.partner`.
- `legacy_credit_code` exists on `res.partner`.
- `legacy_tax_no` exists on `res.partner`.
- `legacy_deleted_flag` exists on `res.partner`.
- `legacy_source_evidence` exists on `res.partner`.

## Write-Mode Preconditions

All of the following must be true before partner write mode starts:

1. A new task contract explicitly authorizes partner small-sample create-only write.
2. The allowed paths include only the dedicated write script, artifacts, docs, and reports.
3. The input must be `artifacts/migration/partner_rebuild_importer_rows_v1.csv`.
4. The input row decision must be `create_candidate`.
5. The row must have non-empty `legacy_partner_id`.
6. The row source must be `T_Base_CooperatCompany`.
7. The target Odoo database must be declared by `DB_NAME`.
8. The write script must refuse update/upsert in the first write batch.
9. The script must emit a post-write lock list keyed by `legacy_partner_source + legacy_partner_id`.
10. A rollback dry-run task must be the immediate next batch after write.

## Idempotency Key

Primary key:

- `legacy_partner_source`
- `legacy_partner_id`

For this strong-evidence slice:

- `legacy_partner_source = cooperat_company`
- `legacy_partner_id = T_Base_CooperatCompany.Id`

Name, credit code, and tax number are not allowed as primary idempotency keys in the first write batch because coverage and ambiguity are not strong enough.

## Allowed Write Fields

The first write batch may only write:

- `name`
- `company_type`
- `legacy_partner_id`
- `legacy_partner_source`
- `legacy_partner_name`
- `legacy_credit_code`
- `legacy_tax_no`
- `legacy_deleted_flag`
- `legacy_source_evidence`

## Forbidden Write Fields

The first write batch must not write:

- bank accounts
- supplier qualifications
- supplier categories
- addresses
- contacts
- contract partner links
- payment, receipt, settlement, invoice, or account data
- cross-source merge decisions
- deleted legacy partners

## Go / No-Go

Current status: `NO-GO for write mode`.

Gate status: write mode can be proposed next, but only as a dedicated create-only sample write batch with explicit user authorization.
