# Lane promotion sequence v1

Status: FROZEN  
Iteration: `ITER-2026-04-14-0027`

This is the forced lane order for the migration program after the project lane
baseline was completed in `sc_demo`.

## Sequence

| Priority | Lane | Current status | Next allowed movement |
| --- | --- | --- | --- |
| P0 | `project` | `BASELINE_READY_FOR_DOWNSTREAM_MAPPING` at 755 rows | no further expansion; only authorized correction batches |
| P1 | `partner` | next lane | L1 dry-run, dedup, safe slice |
| P2 | `project_member` | permission-sensitive | mapping and permission-impact dry-run only |
| P3 | `contract` | NO-GO | dry-run to establish identity, project mapping, partner mapping, amount strategy |
| P4 | `receipt` | stopped | no action before upstream partner/member/contract readiness |
| P5 | `payment / settlement` | stopped high-risk financial lane | no action before dedicated financial semantics task line |
| P6 | `file index` | stopped | no action before business identity lanes are stable |
| P7 | `file binary` | stopped | no action before file index is validated |

## Lane Rules

- One batch may operate on only one lane.
- No write batch may mix two model lanes.
- Downstream lanes consume project baseline identities by
  `project.legacy_project_id`.
- Permission-sensitive lanes must start with dry-run and authority impact
  analysis.
- Financial lanes remain stopped until a dedicated payment/settlement boundary
  recovery task exists.

## Project Lane Freeze

```text
status = BASELINE_READY_FOR_DOWNSTREAM_MAPPING
rules:
- no more sample expansion
- no mixed-model write with other lanes
- only authorized correction batches may change project migration facts
- downstream lanes may consume the project baseline for mapping
```

## Immediate Next Lane

The next executable migration lane is `partner`, starting at L1 dry-run. The
first partner dry-run must produce:

- unified partner shape
- duplicate groups
- merge strategy
- `partner_safe_slice_v1.csv`
- no DB writes
