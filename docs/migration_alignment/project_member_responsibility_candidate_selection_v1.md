# Project member responsibility candidate selection v1

Status: PASS  
Iteration: `ITER-2026-04-14-0030ZC2`

## Purpose

Classify consolidated project/user pairs by responsibility-candidate evidence
strength.

This is not a promotion write. It does not assign `role_key`, write
`project.responsibility`, or change permission semantics.

## Levels

| Level | Rule | Meaning |
| --- | --- | --- |
| L0 | all consolidated pairs | baseline review pool |
| L1 | `evidence_count >= 2` | weak candidate |
| L2 | `evidence_count >= 3 and multi_batch` | strong candidate |
| L3 | `evidence_count >= 4` | priority candidate |

The optional key-project rule is not enabled in this batch because no key-project
list has been frozen.

## Promotion Readiness

Candidate level is evidence strength, not promotion readiness.

Current promotion still requires a verified role source. Pairs without role facts
remain:

```text
promotion_ready = false
requires_role_source = true
```

## Result

| Level | Count |
| --- | ---: |
| L0 | 242 |
| L1 | 110 |
| L2 | 0 |
| L3 | 10 |

Additional result:

| Item | Count |
| --- | ---: |
| total pairs | 362 |
| promotion ready pairs | 0 |
| requires role source pairs | 362 |
| db writes | 0 |

## Outputs

```text
artifacts/migration/project_member_responsibility_candidates_v1.json
artifacts/migration/project_member_responsibility_candidates_v1.csv
artifacts/migration/project_member_responsibility_candidate_summary_v1.json
```
