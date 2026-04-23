# Legacy Global Attachment Screen v1

Status: `PASS`

This read-only screen matches `BASE_SYSTEM_FILE` against all current business
external-id manifests. It does not generate attachments or copy file binaries.

## Result

- source table: `BASE_SYSTEM_FILE`
- file rows: `126967`
- candidate key values: `154118`
- cross-lane matched file rows: `5723`
- same-lane ambiguous file rows: `0`
- deleted matched file rows: `0`
- DB writes: `0`
- Odoo shell: `false`

## Lane Coverage

| Package | Lane | Target model | Matched files | Matched target records | Same-lane ambiguous files | Decision |
|---|---|---|---:|---:|---:|---|
| project_sc_v1 | project | project.project | 464 | 464 | 0 | candidate_for_attachment_asset |
| partner_sc_v1 | partner | res.partner | 0 | 0 | 0 | no_attachment_match |
| contract_counterparty_partner_sc_v1 | contract_counterparty_partner | res.partner | 0 | 0 | 0 | no_attachment_match |
| receipt_counterparty_partner_sc_v1 | receipt_counterparty_partner | res.partner | 0 | 0 | 0 | no_attachment_match |
| user_sc_v1 | user | res.users | 0 | 0 | 0 | no_attachment_match |
| project_member_sc_v1 | project_member | sc.project.member.staging | 7860 | 7858 | 0 | candidate_for_attachment_asset |
| contract_sc_v1 | contract | construction.contract | 0 | 0 | 0 | no_attachment_match |
| contract_line_sc_v1 | contract_line | construction.contract.line | 0 | 0 | 0 | no_attachment_match |
| receipt_sc_v1 | receipt | payment.request | 0 | 0 | 0 | no_attachment_match |
| outflow_request_sc_v1 | outflow_request | payment.request | 0 | 0 | 0 | no_attachment_match |
| actual_outflow_sc_v1 | actual_outflow | payment.request | 5443 | 5443 | 0 | candidate_for_attachment_asset |
| supplier_contract_sc_v1 | supplier_contract | construction.contract | 1 | 1 | 0 | candidate_for_attachment_asset |
| supplier_contract_line_sc_v1 | supplier_contract_line | construction.contract.line | 1 | 1 | 0 | candidate_for_attachment_asset |
| outflow_request_line_sc_v1 | outflow_request_line | payment.request.line | 4689 | 4689 | 0 | candidate_for_attachment_asset |
| receipt_invoice_line_sc_v1 | receipt_invoice_line | sc.receipt.invoice.line | 1079 | 1079 | 0 | candidate_for_attachment_asset |

## Source Match Distribution

| Source field -> candidate key | Matches |
|---|---:|
| PID->attachment_candidate_keys.Id->source_pid | 1079 |
| PID->attachment_candidate_keys.pid | 1079 |
| PID->legacy_actual_outflow_id->source_pid | 5443 |
| PID->legacy_key->source_pid | 464 |
| PID->legacy_member_id->source_pid | 7860 |
| PID->legacy_outflow_line_id->source_pid | 4689 |
| PID->legacy_receipt_invoice_line_id->source_pid | 1079 |
| PID->legacy_supplier_contract_id->source_pid | 2 |
| PID->target_lookup.value->source_pid | 464 |

## Next Attachment Asset Candidates

| Lane | Target model | Matched files | Matched target records |
|---|---|---:|---:|
| project | project.project | 464 | 464 |
| project_member | sc.project.member.staging | 7860 | 7858 |
| actual_outflow | payment.request | 5443 | 5443 |
| supplier_contract | construction.contract | 1 | 1 |
| supplier_contract_line | construction.contract.line | 1 | 1 |
| outflow_request_line | payment.request.line | 4689 | 4689 |

## Decision

Generate attachment URL assets next for `candidate_for_attachment_asset` lanes,
but avoid cross-lane blind merging. If one file matches multiple lanes, each
lane must be generated and verified as a separate package with explicit target
model and dependency.
