# Outflow Request Line Model Carrier v1

Status: `PASS`

This batch adds a structured carrier for legacy outflow request `line_fact`
rows proven by `C_ZFSQGL_CB`.

## Target Model

- model: `payment.request.line`
- parent: `payment.request`
- parent field: `outflow_line_ids`
- source table: `C_ZFSQGL_CB`

## Business Boundary

- `parent_note_not_used`: line facts are not collapsed into parent request notes.
- `ledger_not_used`: line facts do not create payment ledger or paid semantics.
- `settlement_not_used`: line facts do not create settlement semantics.
- `line_fact`: each source line keeps its own stable identity and amount.

## Core Fields

- `request_id`
- `legacy_line_id`
- `legacy_parent_id`
- `legacy_supplier_contract_id`
- `source_document_no`
- `source_line_type`
- `source_counterparty_text`
- `source_contract_no`
- `partner_id`
- `contract_id`
- `amount`
- `paid_before_amount`
- `remaining_amount`
- `current_pay_amount`
- `note`
- `import_batch`

## Decision

Old-system outflow request lines are real business facts. The new system now has
a dedicated target carrier, so later XML asset generation may preserve the
`15917` screened loadable line facts without using parent notes or runtime
ledger/evidence tables.

## Next

Generate `outflow_request_line` XML assets against `payment.request.line` after
verifying parent request anchors and optional partner/contract anchors.
