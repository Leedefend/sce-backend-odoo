# Contract Mapping Dry-Run Master v1

Iteration: `ITER-2026-04-13-1839`

Status: `PASS`

Mode: read-only mapping dry-run, no ORM, no database write.

## Inputs

- Contract source: `tmp/raw/contract/contract.csv`
- Raw project source: `tmp/raw/project/project.csv`
- Known project migration artifacts:
  - `data/migration_samples/project_sample_v1.csv`
  - `artifacts/migration/project_create_only_expand_post_write_snapshot_v1.csv`
- Partner baseline: `artifacts/migration/contract_partner_baseline_v1.json`

## Mapping Summary

| Category | Mapping type | Result |
|---|---|---|
| legacy contract identity | direct | `Id` is unique in 1694 rows |
| project relation | direct via `XMID` then mapping | 146 rows match known written project IDs |
| contract direction | dictionary/text_rule | `out=1554`, `in=1`, `defer=139` |
| partner relation | text_match | exact match rows `0`, defer rows `1694` |
| legacy status | dictionary | defer workflow state; first slice should create draft only |
| deletion marker | dictionary | `DEL=1` must be excluded |
| category | dictionary | defer until contract category dictionary is frozen |
| amount fields | defer | target amount fields are computed from lines and tax |
| contract lines | defer | no target-ready structured line source identified |
| attachments | defer | attachment refs exist but are outside first slice |

## Dry-Run Result

| Item | Result |
|---|---:|
| Rows | 1694 |
| Raw project matches | 1606 |
| Known written project matches | 146 |
| Direction `out` | 1554 |
| Direction `in` | 1 |
| Direction `defer` | 139 |
| Partner exact matches | 0 |
| Safe skeleton candidates | 0 |

## Field-Type Decision

| Legacy field | Target candidate | Mapping type | Current decision |
|---|---|---|---|
| `Id` | legacy identity field | direct | blocked until target legacy field exists |
| `HTBT` | `subject` | direct | candidate |
| `XMID` | `project_id` | direct + mapping | only if known written project matched |
| `FBF` / `CBF` | `partner_id` | text_match | blocked; exact match rate 0 |
| `f_HTDLRQ` | `date_contract` | direct date parse | candidate after preprocess |
| `f_GCKGRQ` | `date_start` | direct date parse | candidate after preprocess |
| `JGRQ` | `date_end` | direct date parse | candidate after preprocess |
| `DJZT` | `state` | dictionary | defer; use draft only in first slice |
| `DEL` | import filter | dictionary | exclude `DEL=1` |
| `HTLX` | `category_id` | dictionary | defer |
| `GCYSZJ` | amount reference | defer | not direct-write safe |
| `HTYDFKFS` | `note` or legacy terms | text | candidate only after text policy |

## Decision

The dry-run does not produce a writable contract skeleton slice yet.

The next blocking work is field alignment for legacy identity and partner matching strategy. Without those, rollback/upsert and required `partner_id` are not safe.
