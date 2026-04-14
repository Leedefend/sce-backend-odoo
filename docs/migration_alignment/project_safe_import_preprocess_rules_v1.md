# Project Safe Import Preprocess Rules v1

This document does not import legacy data and does not implement preprocessing
code.

## Null And Empty Rules

- Treat `NULL`, `null`, `None`, `none`, `N/A`, `n/a`, and whitespace-only values
  as empty.
- Keep numeric-looking legacy IDs as strings.
- Do not convert `0` to empty. `0` is a meaningful legacy marker for fields such
  as `PRICE_METHOD`, `IS_SHARED_BASE`, `STATE`, and `DEL`.

## Text Cleanup

- Trim leading and trailing whitespace for every column.
- Normalize Windows and old Mac line breaks inside text fields to `\n`.
- For single-line fields, replace embedded line breaks with one space.
- Collapse repeated spaces and tabs to a single space in single-line fields.
- Keep Chinese punctuation and full-width characters unchanged.

## Duplicate Detection Before Import

1. Reject duplicate non-empty `legacy_project_id`.
2. Warn, but do not reject, duplicate `other_system_id` or `other_system_code`
   unless `legacy_project_id` is missing.
3. Treat `PROJECT_CODE` as reference-only in this safe slice; do not use it as
   the primary duplicate key.
4. Use project name only for human diagnostics, not for automatic upsert.

## Text Length Strategy

- Do not truncate `project_profile` or `project_overview`; preserve full text.
- For Char fields, keep the full cleaned text in the preprocessed file and let
  the importer reject values that exceed target field constraints.
- If a later implementation chooses truncation, it must write a separate
  truncation audit column or rejection report. Silent truncation is forbidden.

## Reject Row Conditions

Reject a row from the first safe import if any of the following is true:

- `ID` is empty after cleanup.
- `XMMC` is empty after cleanup.
- Another row has the same cleaned `ID`.
- The row contains malformed CSV structure or shifted columns.
- Required template columns are missing.
- A value would require writing a forbidden target such as `company_id`,
  `project_type_id`, `stage_id`, `lifecycle_state`, `active`, user relations,
  partner relations, contract/tax/account/cost fields, or attachments.

## Non-Reject Warnings

- Empty `PROJECT_CODE`.
- Empty `OTHER_SYSTEM_ID` or `OTHER_SYSTEM_CODE`.
- Empty company, specialty, region, owner, supervision, or user text fields.
- `PROJECT_ENV=测试项目`; warn for sample selection, but do not normalize.
