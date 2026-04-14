# ITER-2026-04-14-0030RD Report

## Summary

Queried old SQL Server `LegacyDb` directly to discover whether project_member
has an authoritative role source outside the exported CSV.

## Changed Files

- `agent_ops/tasks/ITER-2026-04-14-0030RD.yaml`
- `scripts/migration/project_member_legacy_role_source_probe.py`
- `artifacts/migration/project_member_legacy_role_source_probe_v1.json`
- `artifacts/migration/project_member_legacy_role_candidate_tables_v1.csv`
- `docs/migration_alignment/project_member_legacy_role_source_audit_v1.md`
- `docs/migration_alignment/project_member_role_fact_decision_v1.md`
- `docs/migration_alignment/project_member_neutral_membership_option_v1.md`
- `agent_ops/reports/2026-04-14/report.ITER-2026-04-14-0030RD.md`
- `agent_ops/state/task_results/ITER-2026-04-14-0030RD.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-14-0030RD.yaml`
- `python3 -m py_compile scripts/migration/project_member_legacy_role_source_probe.py`
- `python3 scripts/migration/project_member_legacy_role_source_probe.py`
- `python3 -m json.tool artifacts/migration/project_member_legacy_role_source_probe_v1.json`
- `test -s artifacts/migration/project_member_legacy_role_candidate_tables_v1.csv`
- `test -s docs/migration_alignment/project_member_legacy_role_source_audit_v1.md`
- `test -s docs/migration_alignment/project_member_role_fact_decision_v1.md`
- `test -s docs/migration_alignment/project_member_neutral_membership_option_v1.md`
- `python3 -m json.tool agent_ops/state/task_results/ITER-2026-04-14-0030RD.json`
- `make verify.native.business_fact.static`

Result: PASS_WITH_RISK / STOP before write

## Result

- Legacy member table: `dbo.BASE_SYSTEM_PROJECT_USER`
- Legacy member rows: 21390
- Role-like columns on primary member table: 0
- Role-like columns in old DB: 454
- Project/user/role triad candidate tables: 17
- Best triad mapping coverage back to `BASE_SYSTEM_PROJECT_USER`: 0.0

## Decision

No authoritative role source is available for direct
`project.responsibility.role_key` mapping.

Neutral membership carrier is the recommended next design branch. Default-role
write remains blocked because no business approval or risk acceptor exists.

## Next

Open `0030N project_member neutral-membership carrier design` before any
project_member write.
