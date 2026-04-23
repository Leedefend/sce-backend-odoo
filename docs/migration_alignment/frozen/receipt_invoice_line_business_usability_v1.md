# Receipt Invoice Line Business Usability v1

Status: frozen checkpoint

## Scope

This checkpoint exposes `sc.receipt.invoice.line` for native Odoo business use
after XML asset replay.

It does not import receipt invoice line XML assets and does not create
attachment binaries.

## Additive Changes

- `payment.request.receipt_invoice_line_ids`
- finance ACL rows for `sc.receipt.invoice.line`
- tree/form/search views for receipt invoice lines
- finance-center action and menu entry
- receipt request smart button and inline receipt invoice line section

## Business Boundary

Included:

- receipt invoice auxiliary facts
- parent receipt request navigation
- project / partner / contract related context
- native `ir.attachment` relation visibility

Excluded:

- posted accounting invoice truth
- `account.move` creation
- settlement truth
- payment ledger truth
- attachment binary import
- record-rule changes

## Verification

Passed commands:

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-15-MIGRATION-RECEIPT-INVOICE-USABILITY.yaml`
- `python3 -m py_compile addons/smart_construction_core/models/core/payment_request.py`
- `rg -n 'receipt_invoice_line_ids|sc.receipt.invoice.line|action_receipt_invoice_line|view_receipt_invoice_line' addons/smart_construction_core/models/core/payment_request.py addons/smart_construction_core/security/ir.model.access.csv addons/smart_construction_core/views/core/payment_request_views.xml`
- `CODEX_NEED_UPGRADE=1 CODEX_MODULES=smart_construction_core make mod.upgrade MODULE=smart_construction_core DB_NAME=sc_demo`
- `make verify.native.business_fact.static`
- `git diff --check`

Database metadata checks:

- ACL rows for `sc.receipt.invoice.line`: `3`
- registered action: `action_receipt_invoice_line`
- registered menu: `menu_receipt_invoice_line`
- registered views:
  - `view_receipt_invoice_line_tree`
  - `view_receipt_invoice_line_form`
  - `view_receipt_invoice_line_search`

## Next Step

The next migration lane can generate attachment index assets for the 1079
deterministically matched `BASE_SYSTEM_FILE.PID -> C_JFHKLR_CB.pid` files.
