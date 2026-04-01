# ITER-2026-03-31-421 Report

## Summary

- Audited the active enterprise master-data layer for a repository-backed
  workbook `岗位` carrier.
- Confirmed that the current enterprise baseline only supports company,
  primary department, and direct manager on `res.users`.
- Froze the next implementation boundary: add a dedicated platform-level post
  master-data carrier in `smart_enterprise_base` instead of overloading roles
  or departments.

## Changed Files

- `agent_ops/tasks/ITER-2026-03-31-421.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-421.md`
- `agent_ops/state/task_results/ITER-2026-03-31-421.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-421.yaml` -> PASS
- `rg -n "job_id|post_ids|hr\\.job|岗位|职务|position|job" addons/smart_enterprise_base/models addons/smart_enterprise_base/views addons/smart_enterprise_base/data` -> PASS (no repository-backed post carrier found)
- `sed -n '1,220p' addons/smart_enterprise_base/models/res_users.py` -> PASS
- `sed -n '1,220p' addons/smart_enterprise_base/models/hr_department.py` -> PASS
- `sed -n '1,220p' addons/smart_enterprise_base/views/res_users_views.xml` -> PASS
- `sed -n '1,220p' addons/smart_enterprise_base/views/hr_department_views.xml` -> PASS

## Audit Result

Current enterprise master-data carriers:

- `res.users.company_id`
- `res.users.sc_department_id`
- `res.users.sc_manager_user_id`
- `hr.department.company_id`
- `hr.department.sc_manager_user_id`

Not present in the active repository:

- `job_id`
- `post_ids`
- `hr.job`
- any equivalent workbook `岗位` model or user relation

## Frozen Design Boundary

The next implementation batch should add a platform-level post carrier inside
`smart_enterprise_base`:

- a dedicated post master-data model
- a single primary post relation on `res.users`
- user views updated to maintain the primary post alongside company, department,
  and direct manager

The workbook `岗位` semantics must stay separate from:

- departments
- system roles
- permission groups

## Outcome

The repository no longer has ambiguity about where workbook `岗位` should land.

The next implementation batch can proceed without guessing ownership:

- module owner: `smart_enterprise_base`
- layer target: platform master data
- user relation: one primary post

## Risk Analysis

- Classification: `PASS`
- No forbidden path or ACL work was needed.
- The carrier gap is now explicit and implementation-ready.

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-31-421.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-421.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-421.json`

## Next Suggestion

- Implement the platform-level post master-data carrier in
  `smart_enterprise_base` with one primary post field on `res.users`.
