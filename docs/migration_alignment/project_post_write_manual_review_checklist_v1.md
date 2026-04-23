# Project Post-Write Manual Review Checklist v1

## Scope

- Target database: `sc_demo`
- Target model: `project.project`
- Source write trial: `ITER-2026-04-13-1825`
- Review target: 30 created project skeleton records
- Review key: `legacy_project_id`

This checklist does not create, update, or delete records.

## Review Conclusion

Manual review is required before expanding the create-only sample. Automated
read-only checks found all 30 records, with no missing or duplicate
`legacy_project_id` values, but also found default `stage_id` values on all 30
records. The `stage_id` result should be reviewed as Odoo defaulting behavior
before expansion.

## Required Manual Checks

| Check | Required result |
| --- | --- |
| Record count | 30 project records visible in `sc_demo` |
| Identity | each record has one of the 30 approved `legacy_project_id` values |
| Name | project names match the sample intent and are readable |
| Raw legacy company text | appears only as raw legacy fields, not formal company relation mapping |
| Raw specialty text | appears only as raw legacy fields, not formal specialty relation mapping |
| Project environment | raw text is acceptable, including the known test-project sample |
| Official project code | no legacy `PROJECT_CODE` was forced into official project code |
| Relations | no manual assumption that `company_id`, specialty, users, or partners were mapped |
| Stage | confirm whether system default `stage_id` is acceptable for skeleton records |
| Attachments | no attachment files were imported |
| Contracts/payments/suppliers | no dependent business records were imported |

## Review Sampling Method

Review at least:

- first 5 records by `id`;
- the known `PROJECT_ENV=测试项目` row;
- rows with empty `other_system_id`;
- rows from different legacy company text values;
- rows with long names.

## Pass Criteria

The write trial may be considered usable if:

- all 30 records are visible and identifiable by `legacy_project_id`;
- project names are readable;
- raw legacy fields are present for later reconciliation;
- default `stage_id` behavior is accepted;
- no unexpected relation mapping is observed.

## Fail Criteria

Stop expansion if:

- any record is missing;
- any `legacy_project_id` is duplicated;
- any project name is blank;
- any row was created outside the approved 30-row identity set;
- default `stage_id` is considered unacceptable for skeleton imports;
- any contract/payment/supplier/attachment data appears as part of this trial.
