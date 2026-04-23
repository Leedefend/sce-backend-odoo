# Legacy Actual Outflow Carrier Screen v1

Status: `PASS`

This screen freezes how `actual_outflow` facts may enter the replayable target
asset bus. It is not an asset generation batch and performs no DB write.

## Carrier Decision

- source table: `T_FK_Supplier`
- target model: `payment.request`
- carrier decision: `draft_carrier`
- external id pattern: `legacy_actual_outflow_sc_<T_FK_Supplier.Id>`
- raw source rows: `13629`
- loadable source rows: `12463`
- blocked source rows: `1166`

The selected carrier is `draft_carrier`: source-backed actual outflow rows may
be replayed as draft target records that preserve project, counterparty, amount,
date, and source trace facts. This lane does not assert target runtime payment
completion.

## Allowed Fields

- `type`
- `project_id`
- `partner_id`
- `amount`
- `date_request`
- `note`

## Forbidden Runtime Fields

- `state`
- `settlement_id`
- `ledger_line_ids`
- `paid_amount_total`
- `unpaid_amount`
- `is_fully_paid`
- `validation_status`
- `reviewer_id`
- `approved_by_id`

Boundary markers:

| Marker | Value |
|---|---:|
| target_model | `True` |
| type_default_pay | `True` |
| project_required | `True` |
| partner_required | `True` |
| amount_required | `True` |
| state_default_draft | `True` |
| state_write_guard | `True` |
| ledger_runtime_method | `True` |
| contract_optional_guard | `True` |
| settlement_optional_guard | `True` |
| view_runtime_actions_present | `True` |
| state_not_written | `True` |
| ledger_not_written | `True` |
| settlement_not_written | `True` |
| contract_not_required | `True` |
| source_request_anchor_optional | `True` |

## Hard Boundary

- `state_not_written`: target default remains draft.
- `ledger_not_written`: no payment ledger or accounting runtime data is created.
- `settlement_not_written`: no settlement relation is created.
- contract reference remains optional.
- original outflow request anchor remains optional and may be kept in note or manifest trace.

## Decision

Use payment.request as a draft business-fact carrier only. Do not materialize paid/completed state, settlement, ledger, workflow, or accounting semantics in the XML asset lane.

## Next

Generate actual_outflow XML assets for the 12463 loadable rows using the allowed field set, then verify that no forbidden runtime fields appear in generated XML.
