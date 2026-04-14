# Project member consolidated pair projection v1

Status: PASS  
Iteration: `ITER-2026-04-14-0030ZB`

## Purpose

Build the readonly governance projection defined by `0030ZA`.

The projection turns neutral evidence rows into reviewable project/user pairs.
It does not write the database and does not create responsibility or permission
semantics.

## Pair Key

```text
project_id + user_id
```

## Output Shape

Each pair includes:

- `project_id`;
- `project_name`;
- `user_id`;
- `user_name`;
- `evidence_count`;
- `evidence_batches`;
- `first_seen_batch`;
- `last_seen_batch`;
- `role_fact_status`;
- `role_fact_status_summary`;
- `batch_distribution`;
- `duplicate_flag`;
- `evidence_row_ids`;
- `promotion_candidate`.

## Promotion Candidate Rule

Initial lightweight rule:

```text
promotion_candidate = true only when at least one role_fact_status is not missing
```

All current pairs remain `promotion_candidate = false` because all current role
facts are `missing`.

## Result

| Item | Count |
| --- | ---: |
| total pairs | 362 |
| pairs with duplicates | 120 |
| pairs without duplicates | 242 |
| max evidence per pair | 5 |
| role fact missing pairs | 362 |
| promotion candidate pairs | 0 |

## Outputs

```text
artifacts/migration/project_member_consolidated_pairs_v1.json
artifacts/migration/project_member_consolidated_pairs_v1.csv
artifacts/migration/project_member_consolidated_summary_v1.json
```
