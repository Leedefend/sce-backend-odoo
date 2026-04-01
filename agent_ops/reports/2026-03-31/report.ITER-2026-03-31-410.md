# ITER-2026-03-31-410 Report

## Summary

- Added an implementation-ready user baseline import specification to
  `smart_construction_custom/README.md`.
- Froze user import semantics for:
  - primary department
  - additional departments
  - posts
  - system roles
- Explicitly preserved the accepted `4 + 3 + 2` special-user structure.

## Changed Files

- `addons/smart_construction_custom/README.md`
- `agent_ops/tasks/ITER-2026-03-31-410.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-410.md`
- `agent_ops/state/task_results/ITER-2026-03-31-410.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-410.yaml` -> PASS

## Documentation Outcome

The README now defines a concrete user-bootstrap baseline:

- source workbook remains `tmp/用户维护 (1).xlsx`
- effective import population remains `20` users
- accepted special-user buckets remain:
  - `4` multi-department
  - `3` `项目部 only`
  - `2` role-only

The specification now freezes:

- user import fields
- primary vs additional department semantics
- separation between posts and system roles
- preservation rules for accepted special-user cases
- recommended import order after company and department bootstrap

## Why This Batch Matters

This batch moves the customer bootstrap chain from:

- company and department setup

to:

- implementation-ready user import semantics

without yet mutating user records or group assignments.

It keeps the next implementation batch narrow and safer:

- user baseline bootstrap first
- role/ACL handling later

## Risk Analysis

- Risk remained low.
- This batch changed documentation only.
- No user write logic, group assignment logic, ACL, or manifest files were
  modified.

## Rollback

- `git restore addons/smart_construction_custom/README.md`
- `git restore agent_ops/tasks/ITER-2026-03-31-410.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-410.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-410.json`

## Next Suggestion

- Open the next implementation batch for:
  - user baseline bootstrap
  - primary and additional department assignment
- Keep post attachment and system-role attachment additive in that batch.
