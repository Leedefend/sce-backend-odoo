# Project Safe Import Readiness v1

This document does not import legacy data and does not approve a full import.

## Decision

The repository is ready to design a small-sample project skeleton import using
only the frozen safe field slice. It is not ready for a full project import or
for relational/status/financial/contract import.

## What Users Get After Safe Skeleton Import

- A `project.project` record per accepted legacy project row.
- Project name and low-risk descriptive master data.
- Legacy ID and external-system traceability.
- Raw company and specialty labels for later reconciliation.
- Raw project environment, business nature, pricing method, area, address,
  profile, overview, and attachment reference text.

## What Users Still Do Not Get

- Official company relation mapping.
- Official project type/category mapping.
- Lifecycle/stage/status conversion.
- Archive/delete behavior from legacy `DEL`.
- Project manager or technical lead user assignment.
- Owner/supervision partner linking.
- Contracts, payments, suppliers, project members, tasks, attachments, tax,
  bank/account, cost, settlement, or finance facts.
- Direct official `project_code` write from legacy `PROJECT_CODE`.

## Small Sample Trial Decision

Recommended next step: yes, proceed to a small-sample trial design task, but only
in dry-run-first mode and only with the safe template fields.

Recommended sample constraints:

- 10 to 20 rows.
- Include rows with and without `PROJECT_CODE`.
- Include rows from matched and unmatched legacy companies.
- Include one `PROJECT_ENV=测试项目` row only if explicitly marked as a warning
  case.
- Exclude rows where `ID` or `XMMC` is empty.

## Not Approved For Next Round

- Full 755-row import.
- Any write to `company_id`, `project_type_id`, `project_category_id`,
  `stage_id`, `lifecycle_state`, `active`, user relations, partner relations,
  contract/payment/supplier/cost/tax/account fields, or attachments.
