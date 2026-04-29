# Fresh DB Packaged Rebuild Acceptance v1

Status: `PASS_WITH_RECORDED_RESIDUALS`

Date: `2026-04-29`

## Scope

This record covers a new prod-sim database rebuild from the private migration
asset package with packaged replay enabled. The acceptance objective is to
prove the rebuild path does not depend on the old source database or on
runtime-generated adapter payloads.

## Package

- package: `/home/odoo/private/sce-assets/migration_assets_release_20260429T135959Z_baseline.tar.gz`
- sha256: `6ec233be3798c4957b58035de30a5162c9f3a6a6602dbd1ea701f76fc5a65716`
- lock: `docs/migration_alignment/migration_asset_package_lock_v1.json`
- materializes: `migration_assets/` and `artifacts/migration/`
- access policy: private local package only; do not publish to public GitHub Releases.

## Acceptance Run

- database: `sc_prod_sim_asset_pkg_rehearsal_20260429`
- replay mode: `HISTORY_CONTINUITY_USE_PACKAGED_PAYLOADS=1`
- optional privacy lanes: disabled
- optional old downstream recovery lanes: disabled
- final probe: `HISTORY_CONTINUITY_USABILITY_PROBE`
- final status: `PASS`
- final probe result: `missing_models=0`, `zero_critical_counts=0`

## Baseline Fixes Proven

- Partner L4 anchors replayed from packaged payload: `6541`.
- Project anchors replayed from packaged payload: `755`.
- Project member neutral carrier replayed from packaged payload: `21390`, with
  `project_responsibility_writes=0` and unchanged visibility.
- Contract header replayed from authoritative contract XML payload: `1492`.
- Material catalog carrier replayed from packaged payload:
  `130624` categories and `2279734` details.
- Legacy attachment custody and runtime probes completed with `gap_count=0`.
- Runtime carrier probes completed with no missing model gaps for settlement
  adjustment, expense claim, treasury reconciliation, receipt income, payment
  execution, financing loan, general contract, construction diary, material
  catalog, and purchase contract.

## Recorded Residuals

These residuals reproduced consistently on the fresh packaged rebuild. They are
not caused by missing package files and did not block the final usability probe.

- Receipt core: `5320` created from `5355` input rows. The `35` non-created rows
  remain a recorded residual for receipt-core promotion policy review.
- Self funding: `55` rows missing project anchors while `3673` rows were
  created.
- Invoice surcharge: `270` missing partner anchors and `124` missing project
  anchors while `27053` rows were created.
- Supplier contract pricing: `30` missing partner anchors and `11` missing
  project anchors while `5345` rows were created.
- Payment residual and receipt residual are preserved as carrier facts with
  reason counts for deleted, missing-anchor, and not-promoted runtime cases.

## Regression Conclusion

The earlier failures would occur again on a new database if the package lacked
frozen replay artifacts or if the one-click flow required default-off recovery
artifacts. This has been fixed by packaging required `artifacts/migration`
payloads, making old downstream recovery lanes opt-in, and aligning precheck to
the authoritative contract counterparty package.

The successful run is therefore not merely "this database passed"; it proves
the default packaged rebuild path is complete for the current carrier-model
baseline, subject to the recorded residuals above.

## Future Model Upgrade Rule

The carrier models used by this rebuild may later be promoted into system
business models. When that happens, historical rebuild impact must be explicitly
re-evaluated before merge or deployment. In particular:

- do not assume carrier-only residual semantics remain acceptable after a model
  becomes a user-facing system business model;
- re-run packaged rebuild acceptance on a new database;
- reclassify receipt-core, anchor-missing, and residual facts against the new
  business model invariants;
- update this acceptance record and the package lock before release.
