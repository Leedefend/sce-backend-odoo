# Legacy Supplier Contract Carrier Screen v1

Status: `PASS`

This screen freezes how `supplier_contract` facts may enter the replayable
target asset bus. It is not an asset generation batch and performs no DB write.

## Carrier Decision

- source table: `T_GYSHT_INFO`
- target model: `construction.contract`
- carrier decision: `type_in_supplier_expense`
- external id pattern: `legacy_supplier_contract_sc_<T_GYSHT_INFO.Id>`
- raw source rows: `5535`
- loadable source rows: `5301`
- blocked source rows: `234`

The selected carrier is `type_in_supplier_expense`: the existing selection key
`in` means supplier/purchase/expense contract in this system. `type_key_not_renamed`
is intentional because changing the key would be a schema and semantic migration
outside the current assetization lane.

## Allowed Fields

- `legacy_contract_id`
- `legacy_project_id`
- `legacy_document_no`
- `legacy_contract_no`
- `legacy_status`
- `legacy_deleted_flag`
- `legacy_counterparty_text`
- `subject`
- `type`
- `project_id`
- `partner_id`
- `date_contract`
- `note`

## Forbidden Computed Or Runtime Fields

- `name`
- `tax_id`
- `amount_untaxed`
- `amount_tax`
- `amount_total`
- `line_amount_total`
- `amount_change`
- `amount_final`
- `state`
- `line_ids`
- `analytic_id`
- `budget_id`
- `payment_request_count`
- `settlement_count`
- `is_locked`

Boundary markers:

| Marker | Value |
|---|---:|
| target_model | `True` |
| type_out_income_label | `True` |
| type_in_expense_label | `True` |
| type_required | `True` |
| project_required | `True` |
| partner_required | `True` |
| subject_required | `True` |
| legacy_contract_id | `True` |
| legacy_project_id | `True` |
| legacy_document_no | `True` |
| legacy_contract_no | `True` |
| legacy_status | `True` |
| legacy_counterparty_text | `True` |
| default_tax_for_type | `True` |
| type_in_purchase_tax | `True` |
| amount_total_computed | `True` |
| line_amount_total_computed | `True` |
| create_sequence_default | `True` |
| type_in_supplier_expense | `True` |
| type_key_not_renamed | `True` |
| amount_header_not_written | `True` |
| tax_not_written | `True` |
| state_not_written | `True` |
| line_not_written | `True` |

## Hard Boundary

- `type_in_supplier_expense`: supplier contracts use `type="in"`.
- `type_key_not_renamed`: no model selection key change in this migration lane.
- `amount_header_not_written`: header computed amount fields are not written.
- `tax_not_written`: target default tax logic applies for `type="in"`.
- `state_not_written`: target default remains draft.
- `line_not_written`: amount/line materialization is a separate later lane.

## Decision

Use construction.contract as a draft supplier contract header carrier with type=in. Do not rename the selection key and do not write computed amount, tax, state, line, settlement, ledger, or accounting fields.

## Next

Generate supplier_contract XML assets for the 5301 loadable rows using the allowed field set, then verify that no forbidden computed/runtime fields appear in generated XML.
