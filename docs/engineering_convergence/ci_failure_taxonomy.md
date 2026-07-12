# CI Failure Taxonomy

Every failed check must be classified before retrying.

| Class | Meaning | Owner | Required Action |
| --- | --- | --- | --- |
| CODE_DEFECT | Product or test target exposed a real code defect. | Module owner | Fix code, add or update test evidence. |
| TEST_DEFECT | Test expectation is stale, duplicated, or incorrect. | Test owner | Fix test and explain changed assertion. |
| ENVIRONMENT | CI runner, Docker, network, DB, or dependency service failed. | DevOps | Attach runner logs and rerun only after environment action. |
| DATA_FIXTURE | Test data is missing, stale, or not isolated. | Test + module owner | Repair fixture and add fixture validation. |
| FLAKY | Same SHA has nondeterministic results. | Test owner | Add to flaky ledger; fix before promoting to required gate. |
| SECURITY | Secret, dependency, permission, upload, import, or API authorization issue. | Security owner | Treat as P0/P1 by impact; attach security evidence. |
| PERFORMANCE | Gate exceeded agreed duration or P95 target. | Performance owner | Attach timing report and regression comparison. |

## Retry Rule

Do not retry a failed CI run more than once without classification.
