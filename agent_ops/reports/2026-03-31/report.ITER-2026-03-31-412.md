# ITER-2026-03-31-412 Report

## Summary

- Added a manual user baseline bootstrap entry to `smart_construction_custom`.
- Implemented primary-department-only user upsert for the frozen customer user baseline.
- Preserved accepted multi-department users by writing only the primary department and deferring additional departments.

## Changed Files

- `addons/smart_construction_custom/models/security_policy.py`
- `addons/smart_construction_custom/data/security_policy_actions.xml`
- `addons/smart_construction_custom/README.md`
- `agent_ops/tasks/ITER-2026-03-31-412.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-412.md`
- `agent_ops/state/task_results/ITER-2026-03-31-412.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-412.yaml` -> PASS
- `python3 -m py_compile addons/smart_construction_custom/models/security_policy.py addons/smart_construction_custom/hooks.py` -> PASS
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_custom DB_NAME=sc_demo` -> PASS
- `make verify.smart_core` -> PASS

## Implementation Outcome

The module now contains:

- model method:
  - `sc.security.policy.bootstrap_customer_users_primary_departments()`
- server action:
  - `Bootstrap Customer Users (Primary Department Only)`

The implementation currently:

- upserts the frozen `20` meaningful users
- writes:
  - `name`
  - `login`
  - `phone`
  - `active`
  - `company_id`
  - `company_ids`
  - `sc_department_id`

Primary department policy used in this batch:

- single-department users:
  - use the recognized department directly
- accepted multi-department users:
  - use the first confirmed department as primary
- role-only users:
  - keep `sc_department_id = False`

Deferred output kept in the implementation result:

- `deferred_extra_departments`
- `unresolved_departments`

## Why This Batch Matters

This is the first real customer-user bootstrap implementation in the chain.

It turns the frozen workbook baseline into executable system writes while still
respecting the current model boundary:

- primary department only now
- additional-department capability later

## Risk Analysis

- Risk remained low.
- No security XML, ACL CSV, manifest, or enterprise-base model files were touched.
- User bootstrap intentionally excludes:
  - additional-department persistence
  - post persistence
  - system-role persistence
  - ACL changes

Non-blocking warning remains:

- Odoo still emits a docutils warning while parsing the module README during upgrade.
- This did not block module upgrade or runtime verification.

## Rollback

- `git restore addons/smart_construction_custom/models/security_policy.py`
- `git restore addons/smart_construction_custom/data/security_policy_actions.xml`
- `git restore addons/smart_construction_custom/README.md`
- `git restore agent_ops/tasks/ITER-2026-03-31-412.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-412.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-412.json`

## Next Suggestion

- Open the next verification batch to execute and audit the customer bootstrap result in `sc_demo`.
- Keep post attachment and system-role attachment in a later additive batch.
