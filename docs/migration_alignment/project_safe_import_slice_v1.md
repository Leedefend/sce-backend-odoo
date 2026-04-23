# Project Safe Import Slice v1

## Scope

- Fact source: `project_mapping_dry_run_report_v1.md`
- Source CSV: `tmp/raw/project/project.csv`
- Rows observed in dry run: 755
- Target: later project skeleton import into `project.project`

This document freezes the first-round safe import slice. It does not import data
and does not define company, specialty, lifecycle/state, user, partner, contract,
tax, bank, cost, file, or member mappings.

## A. First-Round Allowed Import

Only direct, low-risk project master-data or legacy traceability fields are
allowed.

| Legacy Field | Target Field | Required | Reason |
| --- | --- | --- | --- |
| `ID` | `legacy_project_id` | yes | Unique in 755/755 rows and needed for idempotency. |
| `PID` | `legacy_parent_id` | no | Preserves source hierarchy reference without building hierarchy. |
| `XMMC` | `name` | yes | Minimal project skeleton requires project name. |
| `SHORT_NAME` | `short_name` | no | Low-risk text fact. |
| `PROJECT_ENV` | `project_environment` | no | Preserve raw environment marker only; do not normalize. |
| `SPECIALTY_TYPE_ID` | `legacy_specialty_type_id` | no | Preserve source dictionary key without writing Many2one. |
| `SPECIALTY_TYPE_NAME` | `specialty_type_name` | no | Preserve source label without writing project type/category. |
| `PRICE_METHOD` | `legacy_price_method` | no | Preserve raw pricing code only; no pricing behavior. |
| `COMPANYID` | `legacy_company_id` | no | Preserve source company ID without writing `company_id`. |
| `COMPANYNAME` | `legacy_company_name` | no | Preserve source company name without writing `company_id`. |
| `NATURE` | `business_nature` | no | Low-risk raw text fact. |
| `DETAIL_ADDRESS` | `detail_address` | no | Low-risk address text. |
| `PROFILE` | `project_profile` | no | Low-risk descriptive text. |
| `AREA` | `project_area` | no | Preserve raw area text; do not parse units. |
| `IS_SHARED_BASE` | `legacy_is_shared_base` | no | Preserve raw marker; no workflow behavior. |
| `SORT` | `legacy_sort` | no | Preserve raw sort marker. |
| `FJ` | `legacy_attachment_ref` | no | Preserve attachment reference; no attachment import. |
| `PROJECTOVERVIEW` | `project_overview` | no | Low-risk descriptive text. |
| `PROJECT_NATURE` | `legacy_project_nature` | no | Preserve raw nature marker. |
| `IS_MACHINTERIAL_LIBRARY` | `legacy_is_material_library` | no | Preserve raw marker; no material workflow. |
| `OTHER_SYSTEM_ID` | `other_system_id` | no | Unique when present; useful secondary identity. |
| `OTHER_SYSTEM_CODE` | `other_system_code` | no | Unique when present; useful secondary identity. |

Allowed field count: 22.

## B. First-Round Forbidden Import

These fields must not be written to normalized relational, workflow, financial,
contract, user, partner, or deletion targets in the first safe slice.

| Legacy Field | Forbidden Target / Action | Reason |
| --- | --- | --- |
| `PROJECT_CODE` | `project_code` | Project-code write policy is not approved. Preserve separately only if a legacy-code carrier exists. |
| `SPECIALTY_TYPE_NAME` | `project_type_id`, `project_category_id` | Exact dictionary coverage is only 40.93% by row. |
| `COMPANYID` | `company_id` | Branch company mapping unresolved. |
| `COMPANYNAME` | `company_id` | Branch company mapping unresolved. |
| `CONTRACT_STATUS` | contract/status fields | Contract-adjacent and out of scope. |
| `IS_COMPLETE_PROJECT` | `stage_id`, `lifecycle_state`, `active` | Lifecycle conversion not approved. |
| `TAX_ORGANIZATION_ID` | tax relation | Tax ownership out of scope. |
| `TAX_ORGANIZATION_NAME` | tax relation | Tax ownership out of scope. |
| `ACCOUNT_NAME` | bank/account fields | Bank/account semantics out of scope. |
| `ACCOUNT_NUMBER` | bank/account fields | Bank/account semantics out of scope. |
| `ACCOUNT_BANK` | bank/account fields | Bank/account semantics out of scope. |
| `COST` | cost/budget fields | Cost-control semantics out of scope. |
| `MANAGE_FEE_RATIO` | cost/fee fields | Cost-control semantics out of scope. |
| `DEL` | `active` / delete / archive | 61 deleted rows need policy. |
| `PROJECTMANAGER` | `project_manager_user_id` | Source column empty and user matching is not approved. |
| `TECHNICALRESPONSIBILITY` | `technical_lead_user_id` | Source column empty and user matching is not approved. |
| `OWNERSUNIT` | `owner_id` / partner creation | Source column empty and partner matching is not approved. |
| `SUPERVISIONUNIT` | partner creation/linking | Source column empty and partner matching is not approved. |
| `SUPERVISORYENGINEER` | contact creation/linking | Source column empty and contact matching is not approved. |
| `CONTRACTAGREEMENT` | contract fields | Contract-adjacent and out of scope. |
| `PROJECTFILE` | attachment/file import | Attachment import out of scope. |
| `CONTRACTINGMETHOD` | contract fields | Contract-adjacent and out of scope. |
| `WBHTID` | contract reference/link | Contract-adjacent and out of scope. |
| `XMJDID` | `stage_id` | Source empty and lifecycle mapping not approved. |
| `XMJD` | `stage_id` | Source empty and lifecycle mapping not approved. |
| `SSDQID` | region relation | Source empty and no target region dictionary selected. |
| `SSDQ` | region relation | Source empty and no target region dictionary selected. |
| `STATE` | `lifecycle_state`, `stage_id` | `STATE=0` meaning is not approved. |
| `XQRGZ` | requirement workflow | Requirement workflow ownership out of scope. |
| `XQRGZR` / `XQRGZRID` / `XQRGZXZRID` / `XQRGZXZR` | user/workflow assignment | Requirement workflow ownership out of scope. |

Forbidden field count: 30.

## C. Post-Import Backfill

These can be preserved later or filled after the skeleton import once ownership
and mapping rules are approved.

| Legacy Field | Future Target | Reason |
| --- | --- | --- |
| `PROJECT_CODE` | legacy-code carrier or `project_code` | Needs approved strategy. |
| `NOTE` | description or import note | Target field decision is pending. |
| `LRR` | legacy audit carrier | Audit metadata policy pending. |
| `LRRID` | legacy audit carrier | Audit metadata policy pending. |
| `LRSJ` | legacy audit carrier | Audit metadata policy pending. |
| `XGR` | legacy audit carrier | Audit metadata policy pending. |
| `XGRID` | legacy audit carrier | Audit metadata policy pending. |
| `XGSJ` | legacy audit carrier | Audit metadata policy pending. |
| `OWNERSCONTACT` | `owner_contact` | Direct field exists, but source column is empty in current export. |
| `OWNERSCONTACTPHONE` | `owner_contact_phone` | Direct field exists, but source column is empty in current export. |
| `SUPERVISOPHONE` | `supervision_phone` | Direct field exists, but source column is empty in current export. |

Post-import/backfill field count: 11.
