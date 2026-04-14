# Contract 12-Row Post-Write Review And Rollback Lock v1

## Scope

- Task: `ITER-2026-04-14-0003`
- Future write packet: `artifacts/migration/contract_12_row_write_authorization_packet_v1.json`
- Mode: no-DB governance design

This document does not authorize or perform a contract write.

## Future Post-Write Review

Immediately after a future explicitly authorized 12-row create-only write, run a
readonly review that checks:

- exactly 12 `construction.contract` rows exist for the authorized
  `legacy_contract_id` set
- every created row has `legacy_project_id`, `project_id`, `partner_id`,
  `subject`, `type`, and `legacy_counterparty_text` matching the authorization
  payload
- every created row is `draft`
- no authorized `legacy_contract_id` has duplicate contract rows
- no unauthorized `legacy_contract_id` appears in the rollback target list
- no contract line, payment, or settlement linkage is created by the write slice

## Future Rollback Lock

The rollback target list must be keyed by `legacy_contract_id` and include:

- `contract_id`
- `legacy_contract_id`
- `legacy_project_id`
- `project_id`
- `partner_id`
- `name`
- `subject`
- `type`
- `state`

Rollback eligibility requires:

- the row was created by the authorized 12-row payload
- the row has no contract lines
- the row has no payment or settlement references
- the row is not locked by downstream references
- the row still matches its `legacy_contract_id`

If any eligibility check fails, rollback is blocked and must not be attempted
without a new task line.

## Stop Boundary

The next write-capable step requires separate explicit authorization for a
12-row `construction.contract` create-only write.
