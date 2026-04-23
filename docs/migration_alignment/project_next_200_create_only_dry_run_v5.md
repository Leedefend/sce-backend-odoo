# Project next 200 create-only dry-run v5

Status: PASS  
Iteration: `ITER-2026-04-14-0019`  
Database access: none

## Scope

Generated the next non-overlapping 200-row `project.project` create-only
candidate after excluding already materialized project identities from:

- `artifacts/migration/project_create_only_post_write_snapshot_v1.csv`
- `artifacts/migration/project_create_only_expand_post_write_snapshot_v1.csv`
- `artifacts/migration/project_v2_100_post_write_snapshot.csv`
- `artifacts/migration/project_v3_100_post_write_snapshot.csv`
- `artifacts/migration/project_v4_200_post_write_snapshot.csv`

## Result

| Item | Result |
| --- | ---: |
| raw project rows | 755 |
| already materialized project identities | 530 |
| candidate rows | 200 |
| create | 200 |
| update | 0 |
| error | 0 |
| safe fields | 22 |

## Artifacts

- Candidate CSV: `artifacts/migration/project_next_200_candidate_v5.csv`
- Dry-run result: `artifacts/migration/project_next_200_dry_run_result_v5.json`

## Conclusion

The v5 project candidate is ready for a dedicated 200-row write authorization
packet. No DB write was performed in this batch.
