# Project Model Coverage Audit v1

## Audit Boundary

- Target: `project.project`
- Primary implementation file: `addons/smart_construction_core/models/core/project_core.py`
- Primary form view: `addons/smart_construction_core/views/core/project_views.xml`
- Legacy truth source: `tmp/raw/project/project.csv`

No legacy data was imported. Contract, payment, supplier, ACL, record-rule,
manifest, frontend, and menu changes are outside this audit.

## Covered Before This Batch

| Legacy Field | Current Coverage | Notes |
| --- | --- | --- |
| `XMMC` | `name` | Base project name. |
| `PROJECT_CODE` | `project_code` / `code` | Current generated project code and alias. |
| `OWNERSCONTACT` | `owner_contact` | Existing owner contact text. |
| `PROJECTMANAGER` | `manager_id` / `project_manager_user_id` | Existing user relation fields cover mapped users, not raw legacy text. |
| `TECHNICALRESPONSIBILITY` | `technical_lead_user_id` | Existing user relation covers mapped users, not raw legacy text. |
| `XMJD` / `STATE` | `stage_id` / `lifecycle_state` | Current fields cover normalized stage/state after mapping, not raw legacy values. |
| `COMPANYID` / `COMPANYNAME` | `company_id` | Current relation covers mapped company, not raw legacy values. |

## Implemented In This Batch

| Legacy Field | New Field | Type | Reason |
| --- | --- | --- | --- |
| `ID` | `legacy_project_id` | Char | Import idempotency and traceability. |
| `PID` | `legacy_parent_id` | Char | Preserve legacy hierarchy reference without creating hierarchy. |
| `SHORT_NAME` | `short_name` | Char | Project master-data display fact. |
| `PROJECT_ENV` | `project_environment` | Char | Raw environment/category marker. |
| `SPECIALTY_TYPE_ID` | `legacy_specialty_type_id` | Char | Preserve dictionary source key. |
| `SPECIALTY_TYPE_NAME` | `specialty_type_name` | Char | Preserve dictionary label. |
| `PRICE_METHOD` | `legacy_price_method` | Char | Preserve raw code without changing pricing logic. |
| `COMPANYID` | `legacy_company_id` | Char | Preserve source company key before relation mapping. |
| `COMPANYNAME` | `legacy_company_name` | Char | Preserve source company label before relation mapping. |
| `NATURE` | `business_nature` | Char | Project business nature text. |
| `DETAIL_ADDRESS` | `detail_address` | Char | Project address fact. |
| `PROFILE` | `project_profile` | Text | Project profile text. |
| `AREA` | `project_area` | Char | Preserve raw area value before unit cleanup. |
| `IS_SHARED_BASE` | `legacy_is_shared_base` | Char | Preserve source flag without enabling shared-base workflow. |
| `SORT` | `legacy_sort` | Char | Preserve source order value. |
| `FJ` | `legacy_attachment_ref` | Char | Preserve attachment reference without importing attachments. |
| `PROJECTMANAGER` | `legacy_project_manager_name` | Char | Preserve raw manager name before user mapping. |
| `TECHNICALRESPONSIBILITY` | `legacy_technical_responsibility_name` | Char | Preserve raw technical-responsibility name before user mapping. |
| `OWNERSUNIT` | `owner_unit_name` | Char | Preserve building/owner unit text. |
| `OWNERSCONTACTPHONE` | `owner_contact_phone` | Char | Missing owner phone fact. |
| `SUPERVISIONUNIT` | `supervision_unit_name` | Char | Missing supervision unit fact. |
| `SUPERVISORYENGINEER` | `supervisory_engineer_name` | Char | Missing supervisory engineer fact. |
| `SUPERVISOPHONE` | `supervision_phone` | Char | Missing supervision phone fact. |
| `PROJECTOVERVIEW` | `project_overview` | Text | Missing project overview text. |
| `PROJECT_NATURE` | `legacy_project_nature` | Char | Preserve raw legacy project nature. |
| `IS_MACHINTERIAL_LIBRARY` | `legacy_is_material_library` | Char | Preserve raw material-library flag without enabling workflow. |
| `OTHER_SYSTEM_ID` | `other_system_id` | Char | Cross-system traceability. |
| `OTHER_SYSTEM_CODE` | `other_system_code` | Char | Cross-system traceability. |
| `XMJDID` | `legacy_stage_id` | Char | Preserve stage source key before lifecycle mapping. |
| `XMJD` | `legacy_stage_name` | Char | Preserve stage source label before lifecycle mapping. |
| `SSDQID` | `legacy_region_id` | Char | Preserve region source key before dictionary mapping. |
| `SSDQ` | `legacy_region_name` | Char | Preserve region source label before dictionary mapping. |
| `STATE` | `legacy_state` | Char | Preserve raw state before lifecycle mapping. |

## Still Not Covered

| Legacy Field | Reason Deferred |
| --- | --- |
| `CONTRACT_STATUS` | Contract lifecycle meaning is contract-adjacent and not safe to infer in the project model first round. |
| `IS_COMPLETE_PROJECT` | Requires lifecycle/state mapping decision. |
| `TAX_ORGANIZATION_ID` / `TAX_ORGANIZATION_NAME` | Tax semantics are outside this batch. |
| `ACCOUNT_NAME` / `ACCOUNT_NUMBER` / `ACCOUNT_BANK` | Banking/account semantics are outside this batch. |
| `COST` / `MANAGE_FEE_RATIO` | Cost and fee semantics are financial/cost-control facts and need a dedicated mapping decision. |
| `NOTE` | May map to existing description/chatter/import note; deferred to avoid overwriting existing text behavior. |
| `LRR` / `LRRID` / `LRSJ` / `XGR` / `XGRID` / `XGSJ` | Audit metadata is not implemented until import policy decides whether to preserve raw audit columns. |
| `DEL` | Delete/archive mapping could affect active records and must be decided in import workflow. |
| `CONTRACTAGREEMENT` / `CONTRACTINGMETHOD` / `WBHTID` | Contract-adjacent facts deferred to avoid crossing into contract model semantics. |
| `PROJECTFILE` | File/attachment import is out of scope. |
| `ZSLX` | Meaning unclear from CSV header alone. |
| `XQRGZ` / `XQRGZR` / `XQRGZRID` / `XQRGZXZRID` / `XQRGZXZR` | Requirement confirmation workflow ownership needs a separate semantic screen. |
