# Formal Business Form Productization Standard v1

## Purpose

Formal business forms are the daily work surface of the product.  They must
help users complete a business task, not expose a database table, migration
carrier, or low-code configuration artifact.

This standard defines the default product logic for P1 construction industry
forms and the boundary for P2 customer form preferences, P3 runtime low-code
configuration, and P4 migration or verification tools.

## Product Layer Responsibilities

| Layer | Owns | Must Not Own |
| --- | --- | --- |
| P0 platform | form contract schema, renderer behavior, required-marker semantics, view orchestration protocol, preference overlay mechanics | construction business labels, field ordering for a construction document, customer-specific form taste |
| P1 industry product | standard construction form defaults, business entry semantics, status/action defaults, role-level visibility, standard sections, standard attachments | customer-confirmed custom ordering, tenant-only hidden fields, one-off migration evidence |
| P2 customer product | customer-confirmed form order, hidden fields, labels, role simplification, stable customer baseline preferences | generic platform rules, reusable construction industry defaults |
| P3 low-code runtime | administrator-edited field visibility, order, grouping, labels, versioned runtime overrides | unversioned product facts, hidden migration fixes, irreversible global product changes |
| P4 ops/migration | replay, backfill, audit, verification, temporary repair evidence | long-term form layout, ordinary user-facing field source, product defaults |

When a rule is reusable for all standard construction deployments, it belongs
to P1.  When it reflects one customer or tenant preference, it belongs to P2
or P3.  When it exists only to prove, replay, or debug history, it belongs to
P4 and must not appear in ordinary forms.

## Core Design Logic

1. A form is a business workflow surface, not a field container.
2. The form structure follows the user's task, not the model's physical field
   order.
3. The first screen must answer: what is this document, what state is it in,
   who/what is involved, what amount/date matters, and what can I do next.
4. Details can be deep, but the main path must stay narrow.
5. A model used by multiple business entries must allow entry semantics to
   drive visible labels, defaults, sections, and action context.
6. Source, legacy, migration, import, trace, and verification fields belong in
   internal audit or source-trace sections, never in the ordinary task path.
7. Attachments are business evidence and must be designed as first-class
   sections for document-heavy workflows.
8. List, search, and form views must tell the same story: list for scanning,
   search for locating, form for completing.

## Standard Form Anatomy

Every formal business document form should be organized into these conceptual
zones where the model supports them:

| Zone | Purpose | Typical Content | Placement |
| --- | --- | --- | --- |
| Identity and state | identify the document and current lifecycle | document number, business category, status, owner, company | header or first group |
| Primary business context | let the user decide whether this is the right document | project, counterparty, contract, applicant, department, business date | first screen |
| Key financial or quantity facts | show the numbers that drive the task | amount, tax, quantity, unit price, settlement amount, payment amount | first screen or first tab |
| Task-specific details | capture the actual business rows | lines, materials, invoices, payroll rows, settlement rows | detail tab |
| Status actions and approval | explain next action and decision trail | submit, approve, confirm, cancel, review log | header and approval tab |
| Attachments and evidence | collect business proof | contracts, invoices, vouchers, photos, seals, certificates | dedicated tab or evidence block |
| Notes and collaboration | capture human context | remarks, internal notes, chatter | later tab |
| Source trace and audit | prove historical origin without polluting work | legacy ids, import batch, replay evidence, raw source links | internal/audit tab, role-limited where possible |

The section names can vary by domain, but the responsibilities should remain
stable.  A dense form may use tabs, accordions, or task sections; a small form
may combine zones, but it must not mix migration/audit facts into the primary
business path.

## Density Rules

Field count is not the only measure of quality, but it is a useful risk signal.

| Signal | Meaning | Required Response |
| --- | --- | --- |
| `form_field_count < 50` | normal density | keep first screen focused and labels clear |
| `50 <= form_field_count < 70` | medium density | review first-screen scope and section labels |
| `form_field_count >= 70` | high density, P1 productization risk | split into stable business sections/tabs and identify first-screen fields |
| repeated source/legacy/import fields | trace pollution risk | move to source-trace/audit area or restrict by role |
| no notebook/page on dense forms | single-screen dumping risk | add task-oriented tabs or equivalent contract sections |
| weak group/page labels | scanning risk | add business labels or semantic anchors |

The standard first-screen target for ordinary handling is 12-20 core fields.
This is a product target, not a hard storage limit.  Additional fields belong
in detail tabs, evidence tabs, source-trace sections, or role-specific views.

## Entry Semantics

Actions and menus are product semantics.  If one model supports multiple
business entries, the form must be interpreted through the entry, not only the
model.

Examples:

- `sc.expense.claim` can represent reimbursement, deposit return, repayment,
  deduction payment, or guarantee payment.
- `sc.payment.execution` can represent actual payment registration,
  counterparty payment, or company finance expense.
- `sc.hr.payroll.document` can represent payroll, social insurance, bonus, or
  subsidy.

For such models, P1 defaults must define:

- entry label and purpose
- default business category/context
- primary fields for the entry
- optional fields that should be hidden or moved later for the entry
- status/action wording if it differs by entry
- list/search fields that correspond to the entry's task

## Field Classification

Every field shown on a formal business form should fit one of these classes:

| Class | User Meaning | Default Visibility |
| --- | --- | --- |
| primary identity | document number, name, category, state | first screen |
| business context | project, counterparty, contract, department, applicant | first screen |
| decision fact | amount, date, quantity, tax, status reason | first screen or first tab |
| detail line | rows that make up the document | detail tab |
| workflow fact | approval, submitter, reviewer, next action | header or approval tab |
| evidence | attachments, vouchers, invoices, certificates, photos | evidence tab |
| operational note | remark, internal note, collaboration | notes tab |
| source trace | legacy id, import batch, source table, replay evidence | source/audit tab only |
| technical helper | computed helper, domain helper, invisible ids | hidden unless needed by admin/debug |

Fields with technical prefixes such as `source` or `legacy` are not
automatically forbidden; accepted historical business facts can carry business
meaning.  But if the field's purpose is migration evidence or source-system
diagnostics, it must be outside the ordinary handling path.

## State and Actions

Handling forms must make lifecycle state visible and actionable:

- state/status must be visible before detail fields
- available actions must be next-step oriented, not technical method names
- blocked actions must explain the missing business requirement
- readonly state must be obvious when a document is locked
- approval history must be available without hiding the primary task

If the underlying model has no formal workflow, the form still needs a status
context where the business uses draft/confirmed/done/cancelled semantics.

## Attachments and Evidence

Attachment-heavy forms must not rely only on generic chatter.  The form should
make evidence categories understandable:

- contract or agreement
- invoice or tax document
- payment voucher
- approval material
- certificate or license
- site photo or acceptance photo
- other supporting file

Historical attachment source status may be useful for internal audit, but
ordinary users need business evidence availability, not mirror-job internals.

## List/Form/Search Alignment

For every formal entry:

- list view shows the summary needed for scanning and batch selection
- form view contains all list business fields, unless the list field is a
  hidden domain/helper field
- search view covers user search intent: project, counterparty, date, amount,
  status, document number, owner, and high-frequency business category
- search-only fields must not introduce a business concept absent from both
  list and form

## Role and Complexity

Ordinary handlers, reviewers, finance users, administrators, and auditors do
not need the same complexity.

- ordinary handlers see primary context, decision facts, detail rows,
  attachments, notes, and their next actions
- reviewers see approval context and decision basis
- finance users see settlement, tax, payment, ledger, and reconciliation
  fields needed for their task
- administrators see configuration and exceptional maintenance fields
- auditors see source trace and migration evidence

P1 may provide role-aware defaults.  P2/P3 may simplify further for a tenant.
P4 evidence must not be required for ordinary handling.

## Machine Verification

This standard is enforced progressively.  Current machine-readable entry point:

```bash
make verify.business_form.productization.audit
```

The current audit checks:

- formal business entry count from the operation capability matrix
- form density thresholds
- runtime structure classification
- missing tabs/sections
- weak section labels
- source-trace exposure risk
- status and summary-action cues

The audit writes:

- `artifacts/backend/business_form_productization_audit.json`
- `artifacts/backend/business_form_productization_audit.md`

Future form batches should reduce the P1 queue first, then P2.  A concrete
form change is not complete unless the affected entry has a clear before/after
productization reason and the audit output improves or remains justified.

## First Batch Rule

The first productization batch should focus on P1 high-density entries because
they most directly affect perceived product quality.  For each chosen form:

1. identify the entry semantics
2. define the first-screen field set
3. group remaining fields into task sections
4. move source/audit fields out of the ordinary path
5. confirm state/actions and attachments are visible
6. rerun the productization audit and relevant form gates

Do not use visual polish to hide structural problems.  The form must first be
correct by task, boundary, and ownership.
