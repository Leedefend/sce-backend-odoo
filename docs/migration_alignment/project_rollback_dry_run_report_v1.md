# Project Rollback Dry Run Report v1

## Result

ROLLBACK_READY

## Scope

- Target database: `sc_demo`
- Target model: `project.project`
- Source sample: `artifacts/migration/project_sample_v1.csv`
- Rollback key: `legacy_project_id`
- Result artifact: `artifacts/migration/project_rollback_dry_run_result_v1.json`

This run was read-only. It did not execute delete, create, write, update, or
upsert operations.

## Summary

| Metric | Value |
| --- | ---: |
| total_targets | 30 |
| matched_rows | 30 |
| missing_rows | 0 |
| duplicate_matches | 0 |
| out_of_scope_matches | 0 |

## Precision Answer

If rollback is performed by `legacy_project_id`, the current 30 write-trial
records can be precisely locked.

No rollback target should be selected by project name, company text,
`other_system_id`, `other_system_code`, or legacy project code.

## Risk Answers

| Question | Answer |
| --- | --- |
| 越界风险 | No out-of-scope matches were found in dry-run. |
| 缺失风险 | No missing target identity was found. |
| 重复风险 | No duplicate project match was found. |
| 真实回滚前置条件 | Technically met for target selection, but real deletion still requires a separate explicit delete authorization batch. |

## Stage Summary

| stage_id | stage_name | count |
| ---: | --- | ---: |
| 5 | 筹备中 | 30 |

## Conclusion

Rollback dry-run can precisely target the 30 records created by the write trial.
Real rollback is not authorized in this batch.
