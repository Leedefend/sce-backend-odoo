# Receipt Invoice Line Model Design v1

Status: frozen checkpoint

## Scope

This checkpoint introduces a neutral model carrier for legacy receipt invoice
line facts from `C_JFHKLR_CB`.

The model is `sc.receipt.invoice.line`.

No XML asset package, database replay, ACL, record rule, menu, or view is added
in this batch.

## Why A New Carrier

The receipt invoice screen found:

- raw rows: `4491`
- loadable candidate facts: `4454`
- blocked rows: `37`
- carrier decision: `no_safe_existing_xml_carrier`

Rejected carriers:

- `account.move`: would claim accounting truth and posting semantics.
- `sc.settlement.order.invoice_*`: header placeholder fields cannot preserve
  multiple invoice lines per receipt.
- `payment.request.note`: unstructured text is not replayable business data.

## Model Boundary

Included:

- parent receipt request anchor
- stable legacy invoice line identity
- invoice number and invoice party text
- positive invoice amount
- source amount fields for traceability
- legacy attachment BILLID anchor

Excluded:

- accounting entry truth
- posted invoice truth
- settlement truth
- payment ledger truth
- workflow state

## Attachment Plan

Real receipt invoice facts usually need attachment support. The model therefore
includes:

- `legacy_file_bill_id`: stable legacy file matching anchor
- `attachment_ids`: Odoo-native `ir.attachment` many-to-many linkage
- `attachment_count`: read helper

Attachment binary import remains a later dedicated asset lane. The intended
flow is:

1. Generate receipt invoice line XML assets.
2. Load receipt invoice line records and external IDs.
3. Generate attachment index assets from `BASE_SYSTEM_FILE`.
4. Create `ir.attachment` records or attachment-link records after target line
   external IDs exist.

This keeps file evidence linked to native Odoo attachments while avoiding
embedding large binary/process artifacts in the business fact package.

## Future Batches

1. Add ACL and views for `sc.receipt.invoice.line`.
2. Generate `receipt_invoice_line_sc_v1` XML package.
3. Add attachment index screen for `BASE_SYSTEM_FILE`.
4. Generate attachment assets only after parent business external IDs are stable.
