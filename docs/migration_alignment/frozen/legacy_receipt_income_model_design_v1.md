# Legacy Receipt Income Model Design v1

Status: `PASS`

## Target

Add `sc.legacy.receipt.income.fact` as a neutral historical carrier for receipt and income residual facts that are not already covered by `receipt_sc_v1`.

## Source Basis

The direct legacy-DB screen found:

- raw rows: `14769`
- already assetized rows: `5355`
- residual loadable rows: `7220`
- blocked rows: `2194`
- priority source table: `C_CWSFK_GSCWSR`

## Model Boundary

Included:

- source table and source record id
- source family and direction
- document number/date/state
- project anchor
- optional assetized partner anchor
- legacy partner name
- income category
- source amount
- legacy note and import batch

Excluded:

- `payment.request`
- `account.move`
- payment runtime state
- settlement state
- approval runtime state
- generated accounting or fiscal posting

## Required Facts

- `legacy_source_table`
- `legacy_record_id`
- `source_family`
- `direction`
- `project_id`
- `legacy_project_id`
- positive `source_amount`

## Upgrade

The batch requires `smart_construction_core` module upgrade so Odoo creates the support table.
