# ITER-2026-03-31-408 Report

## Summary

- Added an implementation-ready bootstrap specification for company and
  departments into the module README.
- Standardized:
  - company bootstrap fields
  - department bootstrap fields
  - project-department special rule
  - import order
  - exclusions

## Changed Files

- `addons/smart_construction_custom/README.md`
- `agent_ops/tasks/ITER-2026-03-31-408.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-408.md`
- `agent_ops/state/task_results/ITER-2026-03-31-408.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-408.yaml` -> PASS

## Documentation Outcome

The module README now contains a concrete bootstrap specification covering:

- company creation semantics
- department creation semantics
- `项目部` special handling
- import field recommendations
- import order
- separation between:
  - department
  - post
  - system role

## Key Decisions Frozen

- customer company root:
  - `四川保盛建设集团有限公司`
- formal departments:
  - `经营部`
  - `工程部`
  - `财务部`
  - `行政部`
  - `成控部`
  - `项目部`
- `项目部` remains a formal department with future room for project-side
  independent accounting semantics
- `公司员工` is excluded from department import
- posts and system roles must not be mixed into company/department bootstrap

## Why This Batch Matters

This batch converts the current customer understanding into an implementation
input that can be used later without repeating analysis.

It also creates a safe handoff:

- current batch = documentation/spec only
- later batch = actual addon implementation

## Risk Analysis

- Risk remained low.
- No addon implementation, ACL, security, or manifest files were changed.
- This batch only prepared the bootstrap semantics.

## Rollback

- `git restore addons/smart_construction_custom/README.md`
- `git restore agent_ops/tasks/ITER-2026-03-31-408.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-408.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-408.json`

## Next Suggestion

- Open the first real implementation batch for:
  - company root creation
  - department tree bootstrap
- Keep users, posts, roles, and ACL in later batches.
