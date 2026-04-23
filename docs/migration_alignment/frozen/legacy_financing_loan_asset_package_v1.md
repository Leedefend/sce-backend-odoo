# Legacy Financing Loan Asset Package v1

Status: `PASS`

This package turns project-anchored legacy loan and borrowing facts into replayable XML model data.

## Generated Assets

- package id: `legacy_financing_loan_sc_v1`
- target model: `sc.legacy.financing.loan.fact`
- XML: `migration_assets/30_relation/legacy_financing_loan/legacy_financing_loan_v1.xml`
- asset manifest: `migration_assets/manifest/legacy_financing_loan_asset_manifest_v1.json`
- external id manifest: `migration_assets/manifest/legacy_financing_loan_external_id_manifest_v1.json`
- validation manifest: `migration_assets/manifest/legacy_financing_loan_validation_manifest_v1.json`
- catalog: `migration_assets/manifest/migration_asset_catalog_v1.json`

## Counts

- raw screened rows: `873`
- generated XML records: `318`
- loan registration records: `152`
- borrowing request records: `166`
- excluded management balance snapshots: `496`
- blocked rows: `59`
- DB writes: `0`
- Odoo shell: `false`

## Boundary

Included:

- `ZJGL_ZJSZ_DKGL_DKDJ` rows with project anchor, positive amount, date, and counterparty evidence
- `ZJGL_ZCDFSZ_FXJK_JK` rows with project anchor, positive amount, date, and counterparty evidence

Excluded:

- `D_SCBSJS_ZJGL_ZJSZ_ZJRBB` fund daily balance snapshots
- deleted rows
- rows without assetized project anchor
- rows without positive amount
- rows without document date
- rows without counterparty evidence

## Bus Verification

- package verifier: `PASS`
- asset catalog verifier: `PASS`
- migration asset bus verify-only: `PASS`
- package count after this batch: `22`

## Next Step

The next low-risk migration step is to refresh the remaining business fact screen after package 22, then decide whether the remaining supplier/purchase residual or tender/document auxiliary data should be promoted.
