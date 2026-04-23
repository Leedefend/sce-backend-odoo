# Project Safe Importer Design v1

## Purpose

Design only a later project skeleton importer. This batch does not implement the
importer and does not import data.

## Importer Responsibilities

The future importer may only:

- read the approved safe import template;
- create or update `project.project` records by `legacy_project_id`;
- write safe fields from `project_safe_import_slice_v1.md`;
- write legacy traceability fields;
- emit a dry-run report with created/updated/rejected counts;
- produce a row-level rejection file for required-field and uniqueness failures.

## Explicit Non-Responsibilities

The importer must not:

- map or write `company_id`;
- map or write `project_type_id` or `project_category_id`;
- write `stage_id`, `lifecycle_state`, or `active`;
- match or write user relation fields;
- match or write partner relation fields;
- import contracts, payments, suppliers, project members, or tasks;
- import attachments;
- write tax, bank/account, cost, settlement, or finance fields;
- create dictionary, company, partner, or user records;
- alter menus, views, frontend behavior, ACLs, record rules, or manifests.

## Processing Flow

1. Load the safe import template.
2. Apply preprocessing rules from `project_safe_import_preprocess_rules_v1.md`.
3. Validate required fields: `legacy_project_id`, `name`.
4. Check duplicate `legacy_project_id`.
5. If dry-run mode, compute create/update/reject results without writing.
6. If approved write mode in a later task, upsert by `legacy_project_id`.
7. Write only fields listed in group A of `project_safe_import_slice_v1.md`.
8. Emit summary and row-level rejection artifacts.

## Suggested Future Extension Route

1. Add legacy-code carrier if `PROJECT_CODE` must be preserved without writing
   official `project_code`.
2. Approve company branch mapping.
3. Approve specialty dictionary extension or normalization.
4. Approve lifecycle/stage/state/delete conversion.
5. Add user and partner matching only after source columns contain usable text.
6. Open separate contract/payment/supplier import lines only after project
   skeleton data is stable.
