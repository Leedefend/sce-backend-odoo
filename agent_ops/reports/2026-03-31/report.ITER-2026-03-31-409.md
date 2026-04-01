# ITER-2026-03-31-409 Report

## Summary

- Added a manual, idempotent company-and-department bootstrap entry to
  `smart_construction_custom`.
- Exposed the bootstrap path through a dedicated server action instead of
  install-time hooks.
- Updated the module README so the new implementation boundary is explicit.

## Changed Files

- `addons/smart_construction_custom/models/security_policy.py`
- `addons/smart_construction_custom/data/security_policy_actions.xml`
- `addons/smart_construction_custom/README.md`
- `agent_ops/tasks/ITER-2026-03-31-409.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-409.md`
- `agent_ops/state/task_results/ITER-2026-03-31-409.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-409.yaml` -> PASS
- `python3 -m py_compile addons/smart_construction_custom/models/security_policy.py addons/smart_construction_custom/hooks.py` -> PASS
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_custom DB_NAME=sc_demo` -> PASS
- `make verify.smart_core` -> PASS

## Implementation Outcome

The module now contains a manual bootstrap path:

- model method:
  - `sc.security.policy.bootstrap_customer_company_departments()`
- server action:
  - `Bootstrap Customer Company and Departments`

The implementation is intentionally narrow:

- upserts one company root:
  - `四川保盛建设集团有限公司`
- upserts six root departments under that company:
  - `经营部`
  - `工程部`
  - `财务部`
  - `行政部`
  - `成控部`
  - `项目部`
- only writes:
  - `res.company.name`
  - `res.company.sc_is_active`
  - `hr.department.name`
  - `hr.department.company_id`
  - `hr.department.parent_id`
  - `hr.department.sc_is_active`

It does not yet write:

- user membership
- post attributes
- system roles
- ACL or record rules

## Risk Analysis

- Risk remained low because no security file, ACL CSV, manifest, or hook wiring
  was changed.
- The first verification attempt failed due to an execution mistake:
  `mod.upgrade` and `verify.smart_core` were run concurrently against the same
  database and triggered an Odoo serialization failure.
- After rerunning them sequentially, both commands passed.
- Non-blocking warning remains:
  - Odoo emitted a docutils warning while parsing the module README
  - this did not block module upgrade or runtime verification

## Rollback

- `git restore addons/smart_construction_custom/models/security_policy.py`
- `git restore addons/smart_construction_custom/data/security_policy_actions.xml`
- `git restore addons/smart_construction_custom/README.md`
- `git restore agent_ops/tasks/ITER-2026-03-31-409.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-409.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-409.json`

## Next Suggestion

- Open the next customer-bootstrap batch for:
  - user baseline import semantics
  - primary vs additional department assignment
  - post and system-role attachment
