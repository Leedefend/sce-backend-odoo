# ITER-2026-03-31-431 Report

## Summary

- Re-owned enterprise company, department, and post maintenance to the
  business-admin authority path by using the existing
  `smart_construction_core.group_sc_business_full` carrier.
- Kept `用户设置` under `base.group_system` only, because live repository facts
  show `res.users` write/create ownership is still platform-admin scoped.
- Verified the split in live `sc_demo` and passed `make verify.smart_core`.

## Changed Files

- `AGENTS.md`
- `addons/smart_enterprise_base/security/ir.model.access.csv`
- `addons/smart_enterprise_base/views/menu_enterprise_base.xml`
- `addons/smart_construction_custom/tests/test_business_admin_authority_path.py`
- `agent_ops/tasks/ITER-2026-03-31-431.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-431.md`
- `agent_ops/state/task_results/ITER-2026-03-31-431.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-431.yaml` -> PASS
- `python3 -m py_compile addons/smart_construction_custom/tests/test_business_admin_authority_path.py` -> PASS
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_enterprise_base DB_NAME=sc_demo` -> PASS
- live Odoo shell assertion for enterprise-maintenance ownership split -> PASS
- `make verify.smart_core` -> PASS

## Outcome

Enterprise-maintenance ownership now has an explicit split:

- business-admin path (`smart_construction_core.group_sc_business_full`):
  - `公司管理`
  - `组织架构`
  - `岗位管理`
- platform-admin path (`base.group_system` only):
  - `用户设置`

Live verification result:

- `company_action_business_full = True`
- `department_action_business_full = True`
- `post_action_business_full = True`
- `user_action_business_full = False`
- `user_action_system_only = True`
- `acl_company_business_full = True`
- `acl_department_business_full = True`
- `acl_post_business_full = True`
- `acl_users_business_full = False`

This keeps the customer-delivery maintenance chain additive and scoped:

- company / department / post are now available to the business-admin authority
  path inherited by `group_sc_role_business_admin`
- `res.users` ownership was intentionally left outside this batch

## Risk Analysis

- Classification: `PASS`
- This was a high-risk governed batch because it touched ACL and entry
  ownership, but the final change stayed additive and did not leak
  `base.group_system` into the business-admin path.

## Rollback

- `git restore AGENTS.md`
- `git restore addons/smart_enterprise_base/security/ir.model.access.csv`
- `git restore addons/smart_enterprise_base/views/menu_enterprise_base.xml`
- `git restore addons/smart_construction_custom/tests/test_business_admin_authority_path.py`
- `git restore agent_ops/tasks/ITER-2026-03-31-431.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-431.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-431.json`

## Next Suggestion

- Open the next governance batch only if you want to decide whether `用户设置`
  should stay platform-admin-only or enter a separate, even more tightly
  governed `res.users` ownership line.
