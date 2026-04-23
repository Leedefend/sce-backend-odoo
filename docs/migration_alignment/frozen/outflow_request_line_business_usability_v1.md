# Outflow Request Line Business Usability v1

Status: frozen checkpoint

## Scope

This checkpoint completes the business usability surface for
`payment.request.line`, the domain carrier introduced for legacy outflow request
line facts from `C_ZFSQGL_CB`.

The batch is intentionally limited to:

- finance ACL entries for `payment.request.line`
- native Odoo tree/search exposure for payment request lines
- embedded payment request line editing on `payment.request`

It does not change ledger, settlement, accounting, record-rule, or manifest
semantics.

## Architecture Decision

Layer Target: Domain business-fact layer

Module: `smart_construction_core`

Module Ownership: construction finance domain

Kernel or Scenario: scenario

Reason: migrated line facts must be operationally usable after replay. The
missing surface is domain-owned access and native Odoo view exposure, not a
frontend-specific workaround.

## ACL Policy

The carrier follows the existing finance capability path:

- finance manager: read/write/create/delete
- finance user: read/write/create
- finance read: read-only

No record rules are introduced in this batch.

## View Policy

`payment.request.line` is available through:

- a standalone finance menu entry: `付款申请明细`
- a searchable tree view grouped by payment request, project, or contract
- a standalone form view for imported line facts
- an embedded editable line table inside the payment request form

The views keep legacy identifiers visible as read-only trace anchors while
allowing finance users to maintain business fields that are valid in the new
model.

Ordinary UI creation is disabled because `legacy_line_id` and `legacy_parent_id`
are required replay anchors. New line facts should be created by XML/loader
replay, then reviewed or maintained through the finance views.

## Replay Impact

After module upgrade, XML/loader replay can create `payment.request.line`
records linked to `payment.request`. Users with finance access can inspect and
maintain the imported line facts without using technical menus.

## Boundary

This checkpoint does not assert that line amounts are paid, settled, or posted.
Trace values such as historical paid-before and remaining amounts remain legacy
context facts only. Real payment and settlement truth remains owned by the
existing ledger and settlement models.

## Load Order Recovery

The `outflow_line_ids` parent field is owned by the native
`payment.request` model file. The support carrier file only defines
`payment.request.line`.

This avoids extending `payment.request` from a support file before the parent
model is built during registry loading.
