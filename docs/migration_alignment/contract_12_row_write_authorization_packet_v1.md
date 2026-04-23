# Contract 12-Row Write Authorization Packet v1

## Scope

- Task: `ITER-2026-04-14-0002`
- Target DB: `sc_demo`
- Mode: no-DB authorization packet
- Payload: `artifacts/migration/contract_12_row_write_authorization_payload_v1.csv`
- Packet JSON: `artifacts/migration/contract_12_row_write_authorization_packet_v1.json`

## Packet Result

- Payload rows: 12
- Blocked rows: 0
- Operation proposed for a future batch: `construction.contract` create-only
- Contract write authorization: not granted

## Allowed Future Write Fields

- `legacy_contract_id`
- `legacy_project_id`
- `project_id`
- `partner_id`
- `subject`
- `type`
- `legacy_contract_no`
- `legacy_document_no`
- `legacy_external_contract_no`
- `legacy_status`
- `legacy_deleted_flag`
- `legacy_counterparty_text`

The future write batch must let the model sequence assign `name` and must use
the model default tax policy for `tax_id`, as validated by the readonly DB
precheck.

## Explicitly Forbidden In This Slice

- update
- unlink
- workflow replay
- contract line creation
- payment linkage
- settlement linkage

## Authorization Boundary

This packet is not a write authorization.

The next contract write batch may start only after separate explicit
authorization for the 12-row `construction.contract` create-only write.
