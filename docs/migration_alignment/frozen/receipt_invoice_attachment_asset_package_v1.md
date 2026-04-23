# Receipt Invoice Attachment Asset Package v1

Status: frozen checkpoint

## Scope

This checkpoint turns deterministic legacy receipt invoice attachment links into
replayable URL-type `ir.attachment` XML records.

No binary file content is copied into the repository and no target database
business data is imported in this batch.

## Package

- asset package: `receipt_invoice_attachment_sc_v1`
- source table: `BASE_SYSTEM_FILE`
- target model: `ir.attachment`
- related business model: `sc.receipt.invoice.line`
- dependency: `receipt_invoice_line_sc_v1`
- XML: `migration_assets/30_relation/receipt_invoice_attachment/receipt_invoice_attachment_v1.xml`
- asset manifest: `migration_assets/manifest/receipt_invoice_attachment_asset_manifest_v1.json`
- external-id manifest: `migration_assets/manifest/receipt_invoice_attachment_external_id_manifest_v1.json`
- validation manifest: `migration_assets/manifest/receipt_invoice_attachment_validation_manifest_v1.json`

## Result

- source file rows screened: `126967`
- URL attachment records: `1079`
- matched receipt invoice lines: `1079`
- matching rule: `BASE_SYSTEM_FILE.PID -> C_JFHKLR_CB.pid`
- DB writes: `0`
- Odoo shell: `false`

## Boundary

Included:

- `ir.attachment` metadata
- `type=url`
- `res_model=sc.receipt.invoice.line`
- `res_id` reference to receipt invoice line external ID
- legacy file ID, PID, MD5, and size in manifest evidence

Excluded:

- `datas`
- `raw`
- `db_datas`
- `store_fname`
- binary file custody
- file copy into repository

## Verification

Passed commands:

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-15-MIGRATION-RECEIPT-INVOICE-ATTACHMENT-ASSET-PACKAGE.yaml`
- `python3 -m py_compile scripts/migration/legacy_receipt_invoice_attachment_asset_generator.py scripts/migration/legacy_receipt_invoice_attachment_asset_verify.py scripts/migration/migration_asset_bus.py scripts/migration/migration_asset_catalog_verify.py scripts/migration/migration_asset_coverage_snapshot.py`
- `python3 scripts/migration/legacy_receipt_invoice_attachment_asset_generator.py --asset-root migration_assets --expected-ready 1079 --check`
- `python3 scripts/migration/legacy_receipt_invoice_attachment_asset_verify.py --asset-root migration_assets --lane receipt_invoice_attachment --check`
- `python3 scripts/migration/migration_asset_catalog_verify.py --asset-root migration_assets --catalog migration_assets/manifest/migration_asset_catalog_v1.json --check`
- `python3 scripts/migration/migration_asset_bus.py --asset-root migration_assets --catalog migration_assets/manifest/migration_asset_catalog_v1.json --verify-only --check`
- `python3 scripts/migration/migration_asset_coverage_snapshot.py --asset-root migration_assets --catalog migration_assets/manifest/migration_asset_catalog_v1.json --check`
- `git diff --check`

## Rebuild Note

This package lets a fresh Odoo database rebuild the attachment records and their
business-object linkage. The file bytes still require an external file-custody
plan, such as a mounted legacy evidence directory, object storage, or a later
binary import lane.
