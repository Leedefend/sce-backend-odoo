# Project Mapping Dry Run Master v1

## Scope

- Task: `ITER-2026-04-13-1818`
- Source: `tmp/raw/project/project.csv`
- Rows scanned: 755
- Target model: `project.project`
- Runtime reference DB: `sc_demo`

This is a dry run only. No legacy data was imported, no import script was
created, and no model/view/menu/ACL/contract/payment/supplier changes were made.

## Field Mapping Types

| Mapping Type | Meaning |
| --- | --- |
| `direct` | CSV value can be copied to an aligned raw/carrier field. |
| `dictionary` | CSV value must map to an existing Odoo dictionary or relational target. |
| `text_match` | CSV text must be matched against users or partners with candidate confidence. |
| `defer` | Mapping is intentionally held for a later semantic or ownership decision. |

## Master Mapping

| Legacy Field | Target | Type | Dry-Run Decision |
| --- | --- | --- | --- |
| `ID` | `legacy_project_id` | direct | 755/755 non-empty and unique. Use as import idempotency key. |
| `PID` | `legacy_parent_id` | direct | 752/755 non-empty and unique. Preserve only; do not build hierarchy in first import. |
| `XMMC` | `name` | direct | Project name. Required target value. |
| `PROJECT_CODE` | `project_code` | defer | 479 non-empty and unique, but project-code sequence policy must be decided before writing. |
| `SHORT_NAME` | `short_name` | direct | Copy as text when present. |
| `PROJECT_ENV` | `project_environment` | direct | Copy raw value; optional normalized classification is documented separately. |
| `SPECIALTY_TYPE_ID` | `legacy_specialty_type_id` | direct | Preserve source dictionary key. |
| `SPECIALTY_TYPE_NAME` | `specialty_type_name`; candidate `project_type_id` / `project_category_id` | dictionary | Only exact dictionary coverage is safe automatically. |
| `PRICE_METHOD` | `legacy_price_method` | direct | Preserve `0`/`1` raw code; no pricing behavior change. |
| `CONTRACT_STATUS` | none | defer | Contract-adjacent. |
| `IS_COMPLETE_PROJECT` | none | defer | Needs lifecycle conversion rule. |
| `COMPANYID` | `legacy_company_id`; candidate `company_id` | dictionary | Preserve raw ID and map company separately. |
| `COMPANYNAME` | `legacy_company_name`; candidate `company_id` | dictionary | Exact match available for main company only. |
| `NATURE` | `business_nature` | direct | Copy raw value; normalized class is documented separately. |
| `TAX_ORGANIZATION_ID` | none | defer | Tax ownership out of scope. |
| `TAX_ORGANIZATION_NAME` | none | defer | Tax ownership out of scope. |
| `ACCOUNT_NAME` | none | defer | Bank/account semantics out of scope. |
| `ACCOUNT_NUMBER` | none | defer | Bank/account semantics out of scope. |
| `ACCOUNT_BANK` | none | defer | Bank/account semantics out of scope. |
| `DETAIL_ADDRESS` | `detail_address` | direct | Copy as text. |
| `PROFILE` | `project_profile` | direct | Copy as text. |
| `AREA` | `project_area` | direct | Copy raw value; do not parse unit/number yet. |
| `COST` | none | defer | Cost semantics out of scope. |
| `MANAGE_FEE_RATIO` | none | defer | Cost/fee semantics out of scope. |
| `IS_SHARED_BASE` | `legacy_is_shared_base` | direct | Copy raw flag; do not enable shared-base workflow. |
| `SORT` | `legacy_sort` | direct | Copy raw value. |
| `NOTE` | none | defer | Need target decision: description vs import note. |
| `FJ` | `legacy_attachment_ref` | direct | Preserve reference; do not import attachments. |
| `LRR` | none | defer | Legacy audit metadata policy needed. |
| `LRRID` | none | defer | Legacy audit metadata policy needed. |
| `LRSJ` | none | defer | Legacy audit metadata policy needed. |
| `XGR` | none | defer | Legacy audit metadata policy needed. |
| `XGRID` | none | defer | Legacy audit metadata policy needed. |
| `XGSJ` | none | defer | Legacy audit metadata policy needed. |
| `DEL` | none | defer | 61 deleted rows need archive/delete import policy. |
| `PROJECTMANAGER` | `legacy_project_manager_name`; candidate `project_manager_user_id` | text_match | Source column is empty in this export. |
| `TECHNICALRESPONSIBILITY` | `legacy_technical_responsibility_name`; candidate `technical_lead_user_id` | text_match | Source column is empty in this export. |
| `OWNERSUNIT` | `owner_unit_name`; candidate `owner_id` / partner | text_match | Source column is empty in this export. |
| `OWNERSCONTACT` | `owner_contact` | direct | Source column is empty in this export. |
| `OWNERSCONTACTPHONE` | `owner_contact_phone` | direct | Source column is empty in this export. |
| `SUPERVISIONUNIT` | `supervision_unit_name`; candidate partner | text_match | Source column is empty in this export. |
| `SUPERVISORYENGINEER` | `supervisory_engineer_name`; candidate contact | text_match | Source column is empty in this export. |
| `SUPERVISOPHONE` | `supervision_phone` | direct | Source column is empty in this export. |
| `CONTRACTAGREEMENT` | none | defer | Contract-adjacent. |
| `PROJECTFILE` | none | defer | File/attachment import out of scope. |
| `PROJECTOVERVIEW` | `project_overview` | direct | Copy as text. |
| `CONTRACTINGMETHOD` | none | defer | Contract-adjacent. |
| `PROJECT_NATURE` | `legacy_project_nature` | direct | Preserve raw value. |
| `IS_MACHINTERIAL_LIBRARY` | `legacy_is_material_library` | direct | Preserve raw marker; no material-library workflow. |
| `WBHTID` | none | defer | External contract reference. |
| `OTHER_SYSTEM_ID` | `other_system_id` | direct | 696/696 non-empty values are unique. |
| `OTHER_SYSTEM_CODE` | `other_system_code` | direct | 696/696 non-empty values are unique. |
| `ZSLX` | none | defer | Meaning unclear from field name/export alone. |
| `XMJDID` | `legacy_stage_id`; candidate `stage_id` | dictionary | Source column is empty in this export. |
| `XMJD` | `legacy_stage_name`; candidate `stage_id` | dictionary | Source column is empty in this export. |
| `SSDQID` | `legacy_region_id` | dictionary | Source column is empty in this export; no target region dictionary selected. |
| `SSDQ` | `legacy_region_name` | dictionary | Source column is empty in this export; no target region dictionary selected. |
| `STATE` | `legacy_state`; candidate `lifecycle_state` | dictionary | `0` appears in 147 rows; normalized lifecycle meaning is deferred. |
| `XQRGZ` | none | defer | Requirement confirmation workflow ownership needed. |
| `XQRGZR` | none | defer | Requirement confirmation workflow ownership needed. |
| `XQRGZRID` | none | defer | Requirement confirmation workflow ownership needed. |
| `XQRGZXZRID` | none | defer | Requirement confirmation workflow ownership needed. |
| `XQRGZXZR` | none | defer | Requirement confirmation workflow ownership needed. |

## Type Statistics

| Type | Field Count |
| --- | ---: |
| direct | 28 |
| dictionary | 8 |
| text_match | 5 |
| defer | 22 |
| total | 63 |
