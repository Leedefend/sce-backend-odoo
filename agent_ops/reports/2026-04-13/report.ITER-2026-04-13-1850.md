# ITER-2026-04-13-1850 Report

Task: Legacy database full rebuild migration blueprint v1

Status: `PASS`

Decision: `blueprint ready; production rebuild remains NO-GO`

## Architecture

- Layer Target: `Migration Rebuild Blueprint`
- Module: `LegacyDb full business-data reconstruction`
- Module Ownership: `scripts/migration + artifacts/migration + docs/migration_alignment + agent_ops`
- Kernel or Scenario: `scenario`
- Reason: 用户授权直接盘点完整旧库，以完整新库可重复重建为最终目标制定迁移方案。

## Key Facts

- project rows: 755
- project member rows: 21390
- contract rows: 1694
- partner primary source rows: 7864
- supplier rows: 3041
- receipt rows: 7412
- file index rows: 126967
- legacy file index rows: 51964

## Decision

Do not promote one-off scripts to production importers. Use them as probes and dry-run tools until each step passes the rebuild-pipeline promotion gate.

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-13-1850.yaml`: PASS
- `python3 -m py_compile scripts/migration/legacy_db_full_rebuild_blueprint_probe.py`: PASS
- `python3 scripts/migration/legacy_db_full_rebuild_blueprint_probe.py`: PASS
- `python3 -m json.tool artifacts/migration/legacy_db_full_rebuild_blueprint_v1.json`: PASS
- `python3 -m json.tool agent_ops/state/task_results/ITER-2026-04-13-1850.json`: PASS
- `make verify.native.business_fact.static`: PASS

## Next Step

Promote the partner rebuild importer in no-DB mode under the repeatable full-rebuild rules.
