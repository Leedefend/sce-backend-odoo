# Partner dedup strategy v1

Status: L1 DRY-RUN PASS  
Iteration: `ITER-2026-04-14-0028`

This document freezes the partner deduplication priority used by the first
rebuild dry-run importer.

## Dedup Priority

```text
1. tax_number
2. partner_name + phone
3. exact partner_name
```

Rows without a usable identity are excluded from safe-slice selection and must
be handled by a later screening task.

## Group Counts

| Dedup key type | Groups |
| --- | ---: |
| `tax_number` | 3812 |
| `name_phone` | 105 |
| `exact_name` | 3255 |

## Merge Strategy Counts

| Strategy | Groups |
| --- | ---: |
| `create_single` | 3986 |
| `merge_by_tax_number` | 2053 |
| `merge_by_name_phone` | 66 |
| `merge_by_exact_name` | 1067 |

## Duplicate and Conflict Policy

- `duplicate_groups` means more than one source row shares the selected dedup
  key.
- `to_merge` counts duplicate groups that need merge handling.
- Conflict groups are not safe for direct creation.
- Current conflict count: 135.
- Current duplicate group count: 3186.

## Merge Rules

- Same tax number may merge only when names are compatible or manually cleared.
- Same name plus phone may merge when no competing tax number exists.
- Exact name merge is lower confidence and must not override tax evidence.
- Supplier evidence supplements a partner group; it is not a separate primary
  create stream when it matches a company group.
- Conflicts must stay out of bounded-write slices.

## Output Artifacts

- Dry-run result: `artifacts/migration/partner_dry_run_result_v1.json`
- Safe slice: `artifacts/migration/partner_safe_slice_v1.csv`
