# Formal Business Entry Capability Policy

## Purpose

Formal business entries are used for daily business processing after legacy data has been accepted. They must not expose migration evidence, source-system diagnostics, or old-system verification fields to normal users. Fields that already carry business data must be promoted into the formal business surface with business labels instead of being removed because of their technical field names.

## Required Surface

Every formal business entry should provide a consistent set of capabilities where the model supports them:

- list columns for business identity, status, owner, contact summary, and searchable business keys
- form sections for basic information, contact information, accounting or settlement information, business context, attachments, and notes
- search fields for business identity, contact fields, owner, active status, and common classification fields
- filters for active or archived records, company or person records, and high-frequency business classifications
- create and edit defaults that set the entry role, such as customer or supplier rank

## Forbidden User-Visible Fields

Formal business entries must not expose fields whose purpose is only migration verification or source-system tracing:

- old-system identifiers, source tables, source records, import batches, or evidence fields
- old-system visible text fields that duplicate current formal fields

Those fields may remain on the model for audit, replay, and migration support, but they belong in internal audit tools, not formal business menus.

Do not classify a field as forbidden solely from the technical prefix. For example, partner fields such as document status, push result, related project, cooperation type, related business count, receipt amount, payment amount, entry user, and entry time are user-facing business context and should remain visible when they carry accepted business data.

## Partner Master Data Entries

The customer and supplier entries are formal master-data entries. Their visible capability set is:

- basic identity: name, company/person flag, tax code, region, registered capital, business scope, tags, owner, active state
- contact data: phone, mobile, email, address, postal code, website, contacts
- settlement data: account name, bank, account number, payment term, fiscal position
- business context: business role, business basis, unit code, document status, push result, related project, cooperation type, related business count and scope, receipt amount, payment amount, entry user, entry time
- attachments and notes
- customer/supplier role rank defaults

The customer and supplier entries must not show old-system identity fields such as `legacy_partner_id`, `legacy_partner_source`, `legacy_partner_name`, legacy evidence fields, import batches, or legacy bank evidence fields. Business carrier fields may remain visible even when their technical name still starts with `sc_source_`; they should be labeled as formal business fields.

## View Field Matrix

The list, form, and search views should be aligned by business purpose:

- list view: shows the business summary needed for batch checking and selection
- form view: contains every list business field plus detailed maintenance fields
- search view: covers list fields and important form fields used for locating records

For partner master-data entries, every list field must either exist in the form view or be a hidden technical helper required by the action domain. The search view must not introduce a business field that is absent from both the list and form views.

Expected form-only fields include contact lines, bank account line details, attachments, payment terms, fiscal position, address details, website, postal code, and notes that are too detailed for list scanning. These differences are intentional; business carrier fields such as unit code, document status, push result, related project, cooperation type, receipt amount, payment amount, entry user, and entry time should be visible in both the list summary and the form business-information section.

## Business Summary Traceability

Partner fields such as related project, related business count, receipt amount, and payment amount are business summaries. They are not a substitute for the underlying business facts.

When a list view exposes project or amount summaries, the form view must provide a traceable business-detail surface that lets users review the source business rows behind the summary. For customer and supplier entries, this is the related business detail surface with project, business direction, business type, document number, document date, amount, document state, creator, and source record access.

Summary fields on the partner form should be read-only. Daily maintenance belongs to formal master-data fields such as identity, contact, settlement, classification, attachments, and notes. Source business amounts and project associations are maintained through their original business documents and are only summarized on the partner.
