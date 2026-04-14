# ITER-2026-04-14-0030ZA Report

## Summary

Designed the neutral carrier pair-consolidation rule and ran a readonly profile
over the current project_member neutral evidence rows.

## Changed Files

- `agent_ops/tasks/ITER-2026-04-14-0030ZA.yaml`
- `scripts/migration/project_member_neutral_pair_consolidation_profile.py`
- `artifacts/migration/project_member_neutral_pair_consolidation_profile_v1.json`
- `docs/migration_alignment/project_member_neutral_pair_consolidation_v1.md`
- `docs/migration_alignment/project_member_duplicate_evidence_retention_v1.md`
- `docs/migration_alignment/project_member_neutral_to_responsibility_promotion_gate_v1.md`
- `agent_ops/reports/2026-04-14/report.ITER-2026-04-14-0030ZA.md`
- `agent_ops/state/task_results/ITER-2026-04-14-0030ZA.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- neutral carrier = evidence layer;
- consolidated pair = readonly governance projection;
- pair key = `project_id + user_id`;
- duplicate evidence = retained, not deleted;
- raw evidence rows are not formal member responsibility semantics;
- neutral to responsibility promotion is blocked without verified role fact.

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-14-0030ZA.yaml`
- `python3 -m py_compile scripts/migration/project_member_neutral_pair_consolidation_profile.py`
- `DB_NAME=sc_demo make odoo.shell.exec < scripts/migration/project_member_neutral_pair_consolidation_profile.py`
- `python3 -m json.tool artifacts/migration/project_member_neutral_pair_consolidation_profile_v1.json`
- `python3 -m json.tool agent_ops/state/task_results/ITER-2026-04-14-0030ZA.json`
- `make verify.native.business_fact.static`

Result: PASS

## Result

- total evidence rows: 534
- total distinct pairs: 362
- duplicate pair count: 120
- max evidence per pair: 5
- pairs grouped by evidence count: `1=242`, `2=81`, `3=29`, `4=7`, `5=3`
- role fact status grouped by pair: `missing=362`
- db writes: 0

## Risk

Low. This batch is readonly analysis plus documentation. No permission,
record-rule, responsibility, frontend, ACL, or business service logic is changed.

## Next

Proceed to `0030ZB consolidated pair readonly projection`, or continue the next
neutral evidence bounded write batch.
