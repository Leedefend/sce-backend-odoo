# Legacy Fund Daily Snapshot Asset Package v1

Status: `PASS`

This package turns user-required legacy fund daily balance snapshots into replayable XML model data.

## Generated Assets

- package id: `legacy_fund_daily_snapshot_sc_v1`
- target model: `sc.legacy.fund.daily.snapshot.fact`
- XML: `migration_assets/30_relation/legacy_fund_daily_snapshot/legacy_fund_daily_snapshot_v1.xml`
- asset manifest: `migration_assets/manifest/legacy_fund_daily_snapshot_asset_manifest_v1.json`
- external id manifest: `migration_assets/manifest/legacy_fund_daily_snapshot_external_id_manifest_v1.json`
- validation manifest: `migration_assets/manifest/legacy_fund_daily_snapshot_validation_manifest_v1.json`
- catalog: `migration_assets/manifest/migration_asset_catalog_v1.json`

## Counts

- raw screened rows: `873`
- generated XML records: `496`
- excluded loan/borrowing records: `318`
- blocked rows: `59`
- source table: `D_SCBSJS_ZJGL_ZJSZ_ZJRBB`
- DB writes: `0`
- Odoo shell: `false`

## Boundary

Included:

- active `D_SCBSJS_ZJGL_ZJSZ_ZJRBB` rows with project anchor, snapshot date, and at least one non-zero balance/difference amount

Excluded:

- deleted rows
- rows without assetized project anchor
- rows without any balance amount
- loan registration rows already covered by `legacy_financing_loan_sc_v1`
- borrowing request rows already covered by `legacy_financing_loan_sc_v1`

## Bus Verification

- package verifier: `PASS`
- asset catalog verifier: `PASS`
- migration asset bus verify-only: `PASS`
- package count after this batch: `23`

## Next Step

Refresh the remaining business fact screen after package 23, then refresh the detailed judgment matrix before opening the next supplier/purchase residual screen.
