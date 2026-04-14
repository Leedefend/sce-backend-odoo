# Project Create-Only Expansion Write Report v1

Status: PASS  
Iteration: ITER-2026-04-13-1835  
Database: `sc_demo`

## 1. Scope

This batch executed the explicitly authorized 100-row bounded create-only write
using `data/migration_samples/project_expand_candidate_v1.csv`.

It did not perform update/upsert and did not write contract, payment, supplier,
tax, bank, account, cost, settlement, attachment, user, partner, company, or
specialty relation records.

## 2. Write Result

| Item | Result |
| --- | ---: |
| input rows | 100 |
| safe fields | 22 |
| created | 100 |
| updated | 0 |
| errors | 0 |
| post-write identity count | 100 |
| projection mismatches | 0 |

## 3. State Projection Result

All 100 newly created rows were created with:

- `lifecycle_state = draft`
- `stage_id = 5`
- `stage_name = 筹备中`

The post-write validation found `0` rows where `stage_id` differed from the
expected lifecycle projection.

## 4. Artifacts

| Artifact | Path |
| --- | --- |
| write result | `artifacts/migration/project_create_only_expand_write_result_v1.json` |
| pre-write snapshot | `artifacts/migration/project_create_only_expand_pre_write_snapshot_v1.csv` |
| post-write snapshot | `artifacts/migration/project_create_only_expand_post_write_snapshot_v1.csv` |
| input copy | `artifacts/migration/project_expand_candidate_v1.csv` |

## 5. Verification

| Command | Status |
| --- | --- |
| `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-13-1835.yaml` | PASS |
| `python3 -m py_compile scripts/migration/project_create_only_expand_write.py` | PASS |
| `DB_NAME=sc_demo make odoo.shell.exec < scripts/migration/project_create_only_expand_write.py` | PASS |
| `python3 -m json.tool artifacts/migration/project_create_only_expand_write_result_v1.json` | PASS |
| `make verify.native.business_fact.static` | PASS |

## 6. Next Step

Do not expand again immediately. The next safe step is a post-write read-only
review and rollback dry-run lock for these 100 rows.

