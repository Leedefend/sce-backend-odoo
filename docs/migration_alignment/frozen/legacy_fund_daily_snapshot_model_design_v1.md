# Legacy Fund Daily Snapshot Model Design v1

Status: `PASS`

This document freezes the neutral carrier model for user-required legacy fund daily balance snapshots.

## Source Evidence

- source screen: `legacy_fund_loan_residual_screen_v1`
- source table: `D_SCBSJS_ZJGL_ZJSZ_ZJRBB`
- management snapshot candidates: `496`
- prior decision: deferred
- owner decision: user requires fund daily assetization

## Model Boundary

- model: `sc.legacy.fund.daily.snapshot.fact`
- ownership: `smart_construction_core` support business-fact layer
- purpose: carry old-system fund daily balance snapshots as replayable source facts
- not a payment request
- not a settlement record
- not an accounting entry
- not a treasury execution record
- not a bank statement

## Field Design

Core identity:

- `legacy_source_table`
- `legacy_record_id`
- `legacy_pid`
- `import_batch`

Business classification:

- `source_family`: `fund_daily_balance_snapshot`

Snapshot anchors:

- `project_id`
- `legacy_project_id`
- `legacy_project_name`

Snapshot facts:

- `document_no`
- `snapshot_date`
- `legacy_state`
- `subject`
- `source_account_balance_total`
- `source_bank_balance_total`
- `source_bank_system_difference`
- `note`

## Validation Rules

- project or management-subject anchor is required
- legacy project id is required
- snapshot date is required
- at least one source balance or difference amount must be non-zero
- uniqueness is enforced by `(legacy_source_table, legacy_record_id, import_batch)`

## Assetization Readiness

The model is ready for the next asset package batch:

- generate XML for `496` management snapshot candidates
- dependencies should include `project_sc_v1`
- deleted rows and rows without balance amounts remain excluded
- no payment, settlement, accounting, or treasury execution records should be generated

## Verification

- task validation: `PASS`
- model syntax compile: `PASS`
- module registration check: `PASS`
- module upgrade: `PASS`
- note: Odoo warned that the new support model has no ACL. This is expected in this batch because ACL, menu, and view work are explicitly outside scope.

## Rollback

- remove `addons/smart_construction_core/models/support/legacy_fund_daily_snapshot_fact.py`
- remove its import from `addons/smart_construction_core/models/support/__init__.py`
- remove this frozen design document
