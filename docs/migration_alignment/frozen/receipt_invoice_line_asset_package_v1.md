# Receipt Invoice Line Asset Package v1

Status: frozen checkpoint

## Scope

This checkpoint turns legacy receipt invoice line facts from `C_JFHKLR_CB`
into replayable XML assets for `sc.receipt.invoice.line`.

No target database business data is imported in this batch.

## Package

- asset package: `receipt_invoice_line_sc_v1`
- source table: `C_JFHKLR_CB`
- target model: `sc.receipt.invoice.line`
- dependency: `receipt_sc_v1`
- XML: `migration_assets/20_business/receipt_invoice_line/receipt_invoice_line_v1.xml`
- asset manifest: `migration_assets/manifest/receipt_invoice_line_asset_manifest_v1.json`
- external-id manifest: `migration_assets/manifest/receipt_invoice_line_external_id_manifest_v1.json`
- validation manifest: `migration_assets/manifest/receipt_invoice_line_validation_manifest_v1.json`

## Result

- raw rows: `4491`
- loadable records: `4454`
- blocked records: `37`
- amount source: `KPJE = 4454`
- invoice number present: `4490`
- invoice number empty: `1`
- DB writes: `0`
- Odoo shell: `false`

Blocked reason counters:

- `receipt_anchor_missing`: `28`
- `amount_not_positive`: `10`

The reason counters can exceed blocked record count when a single row has more
than one blocker.

## Business Boundary

Included:

- parent receipt request anchor
- legacy invoice line identity
- invoice number and invoice party text
- positive invoice amount
- legacy source IDs for future attachment indexing

Excluded:

- `account.move` / posted accounting invoice truth
- settlement truth
- ledger truth
- attachment binary import

## Attachment Boundary

The package preserves attachment candidate keys in the external-id manifest:

- `Id`
- `ZBID`
- `FPID`
- `FP_CB_Id`
- `pid`

These keys are evidence for the later `BASE_SYSTEM_FILE` attachment-index lane.
This batch does not create `ir.attachment` records and does not embed file
binary data in XML.

## Verification

Passed commands:

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-15-MIGRATION-RECEIPT-INVOICE-ASSET-PACKAGE.yaml`
- `python3 -m py_compile scripts/migration/legacy_receipt_invoice_asset_generator.py scripts/migration/legacy_receipt_invoice_asset_verify.py scripts/migration/migration_asset_bus.py scripts/migration/migration_asset_catalog_verify.py scripts/migration/migration_asset_coverage_snapshot.py`
- `python3 scripts/migration/legacy_receipt_invoice_asset_generator.py --asset-root migration_assets --expected-ready 4454 --check`
- `python3 scripts/migration/legacy_receipt_invoice_asset_verify.py --asset-root migration_assets --lane receipt_invoice_line --check`
- `python3 scripts/migration/migration_asset_catalog_verify.py --asset-root migration_assets --catalog migration_assets/manifest/migration_asset_catalog_v1.json --check`
- `python3 scripts/migration/migration_asset_bus.py --asset-root migration_assets --catalog migration_assets/manifest/migration_asset_catalog_v1.json --verify-only --check`
- `python3 scripts/migration/migration_asset_coverage_snapshot.py --asset-root migration_assets --catalog migration_assets/manifest/migration_asset_catalog_v1.json --check`
- `git diff --check`

## Next Step

The next low-risk migration lane is either:

- receipt invoice line usability exposure: ACL/view/action for business users
- receipt attachment index screen: classify `BASE_SYSTEM_FILE` linkage without
  importing file binaries
