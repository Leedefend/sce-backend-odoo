# Legacy Financing Loan Model Design v1

Status: `PASS`

This document freezes the neutral carrier model for project-anchored legacy loan and borrowing facts.

## Source Evidence

- source screen: `legacy_fund_loan_residual_screen_v1`
- project-anchored financing candidates: `318`
- excluded management snapshots: `496`
- blocked rows: `59`
- source tables: `ZJGL_ZJSZ_DKGL_DKDJ`, `ZJGL_ZCDFSZ_FXJK_JK`

## Model Boundary

- model: `sc.legacy.financing.loan.fact`
- ownership: `smart_construction_core` support business-fact layer
- purpose: carry old-system financing and borrowing facts as replayable source facts
- not a payment request
- not a settlement record
- not an accounting entry
- not a fund-balance snapshot

The 496 rows from `D_SCBSJS_ZJGL_ZJSZ_ZJRBB` remain excluded from this model because they are daily balance snapshots. They may need a separate management snapshot carrier only after a target business requirement is confirmed.

## Field Design

Core identity:

- `legacy_source_table`
- `legacy_record_id`
- `legacy_pid`
- `import_batch`

Business classification:

- `source_family`: `loan_registration`, `borrowing_request`
- `source_direction`: `financing_in`, `borrowed_fund`

Business fact anchors:

- `project_id`
- `legacy_project_id`
- `legacy_project_name`
- `partner_id`
- `legacy_counterparty_id`
- `legacy_counterparty_name`

Amount and timing:

- `source_amount`
- `source_amount_field`
- `document_date`
- `due_date`
- `legacy_state`

Legacy context:

- `document_no`
- `purpose`
- `source_type_label`
- `source_extra_ref`
- `source_extra_label`
- `note`

## Validation Rules

- source amount must be positive
- project anchor is required
- legacy project id is required
- counterparty evidence is required through either an assetized partner or legacy counterparty name
- uniqueness is enforced by `(legacy_source_table, legacy_record_id, import_batch)`

## Assetization Readiness

The model is ready for the next asset package batch:

- generate XML for `318` project-anchored financing candidates only
- dependencies should include `project_sc_v1`
- partner dependency is optional because old data includes personal counterparties and text-only counterparties
- blocked rows stay out of the package
- fund daily balance snapshots stay out of this package

## Verification

- task validation: `PASS`
- model syntax compile: `PASS`
- module registration check: `PASS`
- module upgrade: `PASS`
- note: Odoo warned that the new support model has no ACL. This is expected in this batch because ACL, menu, and view work are explicitly outside scope and require a dedicated permission/usability batch.

## Rollback

- remove `addons/smart_construction_core/models/support/legacy_financing_loan_fact.py`
- remove its import from `addons/smart_construction_core/models/support/__init__.py`
- remove this frozen design document
