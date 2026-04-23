# Project Safe Import Template v1

## Purpose

Define the first-round project skeleton import template. This document does not
generate a real import file and does not execute an import.
It does not import legacy data.

## Template Columns

| Template Column | Target Field | Required | Source Field | Notes |
| --- | --- | --- | --- | --- |
| `legacy_project_id` | `legacy_project_id` | yes | `ID` | Primary upsert key. |
| `legacy_parent_id` | `legacy_parent_id` | no | `PID` | Preserve only. |
| `name` | `name` | yes | `XMMC` | Reject row if empty after trim. |
| `short_name` | `short_name` | no | `SHORT_NAME` | Optional text. |
| `project_environment` | `project_environment` | no | `PROJECT_ENV` | Raw text only. |
| `legacy_company_id` | `legacy_company_id` | no | `COMPANYID` | Do not write `company_id`. |
| `legacy_company_name` | `legacy_company_name` | no | `COMPANYNAME` | Do not write `company_id`. |
| `legacy_specialty_type_id` | `legacy_specialty_type_id` | no | `SPECIALTY_TYPE_ID` | Do not write dictionary relation. |
| `specialty_type_name` | `specialty_type_name` | no | `SPECIALTY_TYPE_NAME` | Raw label only. |
| `legacy_price_method` | `legacy_price_method` | no | `PRICE_METHOD` | Raw code only. |
| `business_nature` | `business_nature` | no | `NATURE` | Raw text only. |
| `detail_address` | `detail_address` | no | `DETAIL_ADDRESS` | Optional text. |
| `project_profile` | `project_profile` | no | `PROFILE` | Optional text. |
| `project_area` | `project_area` | no | `AREA` | Raw value only. |
| `legacy_is_shared_base` | `legacy_is_shared_base` | no | `IS_SHARED_BASE` | Raw flag only. |
| `legacy_sort` | `legacy_sort` | no | `SORT` | Raw sort marker. |
| `legacy_attachment_ref` | `legacy_attachment_ref` | no | `FJ` | No attachment import. |
| `project_overview` | `project_overview` | no | `PROJECTOVERVIEW` | Optional text. |
| `legacy_project_nature` | `legacy_project_nature` | no | `PROJECT_NATURE` | Raw marker only. |
| `legacy_is_material_library` | `legacy_is_material_library` | no | `IS_MACHINTERIAL_LIBRARY` | Raw marker only. |
| `other_system_id` | `other_system_id` | no | `OTHER_SYSTEM_ID` | Secondary identity. |
| `other_system_code` | `other_system_code` | no | `OTHER_SYSTEM_CODE` | Secondary identity. |

## Sample Header

```csv
legacy_project_id,legacy_parent_id,name,short_name,project_environment,legacy_company_id,legacy_company_name,legacy_specialty_type_id,specialty_type_name,legacy_price_method,business_nature,detail_address,project_profile,project_area,legacy_is_shared_base,legacy_sort,legacy_attachment_ref,project_overview,legacy_project_nature,legacy_is_material_library,other_system_id,other_system_code
```

## Excluded From Template

Do not include `company_id`, `project_type_id`, `project_category_id`,
`stage_id`, `lifecycle_state`, `active`, user relation fields, partner relation
fields, contract fields, payment fields, supplier fields, tax/account fields,
cost fields, attachment binaries, or membership rows.
