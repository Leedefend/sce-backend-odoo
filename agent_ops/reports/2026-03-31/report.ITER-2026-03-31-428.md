# ITER-2026-03-31-428 Report

## Summary

- Implemented a platform-level multi-department carrier on `res.users` while
  keeping `sc_department_id` as the single primary department.
- Extended enterprise-base drill-down and user views so primary and extra
  departments are both visible and queryable.
- Closed the deferred workbook `extra_departments` semantics by attaching them
  to live customer users in `sc_demo`.

## Changed Files

- `addons/smart_enterprise_base/models/res_users.py`
- `addons/smart_enterprise_base/models/hr_department.py`
- `addons/smart_enterprise_base/views/res_users_views.xml`
- `addons/smart_construction_custom/models/security_policy.py`
- `addons/smart_construction_custom/data/security_policy_actions.xml`
- `addons/smart_construction_custom/tests/test_business_admin_authority_path.py`
- `agent_ops/tasks/ITER-2026-03-31-428.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-428.md`
- `agent_ops/state/task_results/ITER-2026-03-31-428.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-428.yaml` -> PASS
- `python3 -m py_compile addons/smart_enterprise_base/models/res_users.py addons/smart_enterprise_base/models/hr_department.py addons/smart_construction_custom/models/security_policy.py addons/smart_construction_custom/tests/test_business_admin_authority_path.py` -> PASS
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_enterprise_base DB_NAME=sc_demo` -> PASS
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_custom DB_NAME=sc_demo` -> PASS
- live Odoo shell assertion for `bootstrap_customer_user_extra_departments()` -> PASS
- `make verify.smart_core` -> PASS

## Outcome

Repository-backed multi-department closure now exists:

- `res.users.sc_department_id` remains the primary department
- `res.users.sc_department_ids` carries additive extra departments
- department drill-down now returns users whose primary department or extra
  department matches the selected department
- customer bootstrap now persists the frozen workbook `extra_departments`
  semantics into live user records

Live verification result:

- `updated_user_count = 4`
- `unresolved_users = []`
- `duanyijun_extra_departments = ['行政部']`
- `chenshuai_extra_departments = ['项目部']`

## Risk Analysis

- Classification: `PASS`
- No ACL, record-rule, manifest, or financial-domain changes were required.
- The implementation stayed additive by separating `extra departments` from the
  primary department carrier.

## Rollback

- `git restore addons/smart_enterprise_base/models/res_users.py`
- `git restore addons/smart_enterprise_base/models/hr_department.py`
- `git restore addons/smart_enterprise_base/views/res_users_views.xml`
- `git restore addons/smart_construction_custom/models/security_policy.py`
- `git restore addons/smart_construction_custom/data/security_policy_actions.xml`
- `git restore addons/smart_construction_custom/tests/test_business_admin_authority_path.py`
- `git restore agent_ops/tasks/ITER-2026-03-31-428.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-428.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-428.json`

## Next Suggestion

- Resume customer bootstrap closure by evaluating whether workbook
  `extra_departments` now remove the last unresolved organization-carrier gap
  or whether the next valid batch should move to user-facing organization
  maintenance and audit.
