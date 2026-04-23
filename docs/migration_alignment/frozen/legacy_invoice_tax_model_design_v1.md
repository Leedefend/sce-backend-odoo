# Legacy Invoice Tax Model Design v1

Status: `PASS`

## Target

Add `sc.legacy.invoice.tax.fact` as a neutral historical carrier for legacy invoice and tax facts.

## Source Basis

The direct legacy-DB screen found:

- raw rows: `21323`
- loadable rows: `5920`
- blocked rows: `15403`
- priority source table: `C_JXXP_XXKPDJ`

## Model Boundary

Included:

- source table and source record id
- source family and direction
- document number/date/state
- project anchor
- optional assetized partner anchor
- legacy partner name and tax number
- source amount and tax amount
- source invoice/tax type
- legacy note and import batch

Excluded:

- `account.move`
- tax ledger state
- payment state
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
- `source_amount_field`
- at least one positive value among `source_amount` and `source_tax_amount`
- at least one counterparty evidence among `partner_id`, `legacy_partner_name`, and `legacy_partner_tax_no`

## Upgrade

The batch requires `smart_construction_core` module upgrade so Odoo creates the support table.
