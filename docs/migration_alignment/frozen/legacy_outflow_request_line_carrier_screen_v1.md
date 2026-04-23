# Legacy Outflow Request Line Carrier Screen v1

Status: `PASS_WITH_STOP`

This screen freezes the target-carrier decision for outflow request `line_fact`
rows. It performs no DB write and does not generate XML assets.

## Source Facts

- source table: `C_ZFSQGL_CB`
- raw rows: `17413`
- loadable line facts from screen: `15917`
- blocked/discarded rows: `1496`

## Carrier Decision

`no_safe_existing_xml_carrier`

| Candidate model | Decision | Reason |
|---|---|---|
| payment.request | rejected | parent request has no line fact one2many; note is not a structured replayable line carrier |
| payment.ledger | rejected | ledger is runtime payment evidence and would fabricate payment/paid semantics |
| sc.business.evidence | rejected | requires runtime business_id and allow_evidence_mutation context; not safe as XML carrier |

## Boundary Markers

| Marker | Value |
|---|---:|
| no_safe_existing_xml_carrier | `True` |
| parent_note_not_used | `True` |
| ledger_not_used | `True` |
| business_evidence_not_used | `True` |
| neutral_staging_required | `True` |
| line_fact_preserved | `True` |

## Hard Boundary

- `parent_note_not_used`: line facts must not be collapsed into parent request notes.
- `ledger_not_used`: line facts must not fabricate paid/ledger semantics.
- `business_evidence_not_used`: XML cannot safely populate runtime `business_id` evidence.
- `neutral_staging_required`: a dedicated neutral carrier is required before XML assetization.

## Decision

Do not generate XML assets for outflow_request_line against existing models. A dedicated neutral staging carrier or explicit target line model is required before assetization.

## Next

Open a dedicated model-carrier design task for outflow request line facts, or switch to receipt_invoice line screen while this carrier decision is handled.
