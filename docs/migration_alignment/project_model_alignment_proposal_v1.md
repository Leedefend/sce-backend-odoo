# Project Model Alignment Proposal v1

## Decision

Use a first-round additive project-master-data alignment on `project.project`.

The batch keeps normalized current fields (`project_code`, `company_id`,
`stage_id`, `lifecycle_state`, user relation fields) intact and adds raw legacy
carrier fields where later import needs traceability or manual mapping.

## First-Round Must Add

1. Import identity and source references:
   `legacy_project_id`, `legacy_parent_id`, `other_system_id`,
   `other_system_code`.
2. Dictionary/source mapping helpers:
   `legacy_company_id`, `legacy_company_name`, `legacy_specialty_type_id`,
   `specialty_type_name`, `legacy_stage_id`, `legacy_stage_name`,
   `legacy_region_id`, `legacy_region_name`, `legacy_state`.
3. Project master-data facts:
   `short_name`, `project_environment`, `legacy_price_method`,
   `business_nature`, `detail_address`, `project_profile`, `project_area`,
   `legacy_is_shared_base`, `legacy_sort`, `legacy_attachment_ref`,
   `legacy_project_nature`, `legacy_is_material_library`.
4. Participant/contact facts:
   `legacy_project_manager_name`, `legacy_technical_responsibility_name`,
   `owner_unit_name`, `owner_contact_phone`, `supervision_unit_name`,
   `supervisory_engineer_name`, `supervision_phone`.
5. Project text fact:
   `project_overview`.

## Deferred

- Data import execution.
- Attachment import.
- Search/list/menu expansion.
- Contract, payment, supplier, tax, bank-account, and cost-control semantics.
- Lifecycle conversion of `IS_COMPLETE_PROJECT`, `DEL`, `STATE`, and `XMJD`.
- Legacy audit metadata preservation.
- Requirement confirmation workflow mapping.

## Compatibility

- Existing fields are not renamed or removed.
- New fields are plain stored fields and do not change existing compute,
  constraint, workflow, ACL, record-rule, or contract behavior.
- Form additions are grouped under the existing project construction page.

## Next Proposal

Run a dedicated mapping screen before import to decide:

- company and specialty dictionaries;
- stage/lifecycle/state conversion;
- whether old audit metadata must be preserved;
- whether `NOTE` should map to Odoo description or a dedicated import note;
- how contract-adjacent and cost/account/tax fields should be owned.
