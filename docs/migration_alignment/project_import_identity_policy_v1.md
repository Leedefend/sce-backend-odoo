# Project Import Identity Policy v1

This document does not import legacy data and does not implement an importer.

## Identity Priority

| Priority | Candidate | Use | Decision |
| ---: | --- | --- | --- |
| 1 | `legacy_project_id` | upsert | Primary upsert key. `ID` is 755/755 non-empty and unique. |
| 2 | `other_system_id` | upsert fallback only | 696 non-empty and unique. Use only if `legacy_project_id` is unavailable in a future source. |
| 3 | `other_system_code` | upsert fallback only | 696 non-empty and unique. Use only if both higher-priority IDs are unavailable. |
| 4 | legacy project code / `PROJECT_CODE` | manual reference only in v1 | 479 non-empty and unique, but official write policy is not approved. |
| 5 | project name + company | manual reference only | Company mapping is unresolved and names may change or collide. |

## Upsert Rule

For the first safe import design:

1. Match existing records by `legacy_project_id`.
2. If no match exists, create a project skeleton record.
3. Do not update records by `project_code` in v1.
4. Do not update records by project name alone.
5. Do not update records by company relation because `company_id` is not written
   in this slice.

## Human Reference Fields

These fields can be shown in dry-run/reconciliation reports but must not drive
automatic upsert in v1:

- `PROJECT_CODE`
- `COMPANYNAME`
- `SPECIALTY_TYPE_NAME`
- `XMMC`
- `OTHER_SYSTEM_ID` and `OTHER_SYSTEM_CODE` when `legacy_project_id` is present

## Rejection Rule

Reject any row that lacks `legacy_project_id` in the first safe sample import.
Do not silently fall back to name matching.
