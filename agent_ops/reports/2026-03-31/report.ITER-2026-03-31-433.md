# ITER-2026-03-31-433 Report

## Summary

- Re-owned `用户设置` to the business-admin authority path by adding the
  business-full ACL and exposing the enterprise user-maintenance action/menu to
  `smart_construction_core.group_sc_business_full`.
- Kept the enterprise user-maintenance view scoped to enterprise master-data
  fields only.
- Verified in live `sc_demo` that the page is now business-admin-owned without
  exposing platform governance fields such as `groups_id`, `company_ids`, or
  `sc_role_profile`.

## Changed Files

- `AGENTS.md`
- `addons/smart_enterprise_base/security/ir.model.access.csv`
- `addons/smart_enterprise_base/views/menu_enterprise_base.xml`
- `addons/smart_construction_custom/tests/test_business_admin_authority_path.py`
- `agent_ops/tasks/ITER-2026-03-31-433.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-433.md`
- `agent_ops/state/task_results/ITER-2026-03-31-433.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-433.yaml` -> PASS
- `python3 -m py_compile addons/smart_construction_custom/tests/test_business_admin_authority_path.py` -> PASS
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_enterprise_base DB_NAME=sc_demo` -> PASS
- live Odoo shell assertion for enterprise user-maintenance ownership -> PASS
- `make verify.smart_core` -> PASS

## Outcome

Enterprise maintenance ownership now fully matches the accepted customer
boundary:

- business-admin path (`smart_construction_core.group_sc_business_full`):
  - `公司管理`
  - `组织架构`
  - `岗位管理`
  - `用户设置`
- platform-admin path (`base.group_system`):
  - still present as a parallel owner, but no longer the only owner

Live verification result:

- `user_action_business_full = True`
- `user_menu_business_full = True`
- `user_action_system_group = True`
- `acl_users_business_full = True`
- `contains_groups_field = False`
- `contains_company_ids_field = False`
- `contains_role_profile_field = False`

Visible enterprise user fields remain:

- `name`
- `login`
- `phone`
- `active`
- `company_id`
- `sc_department_id`
- `sc_department_ids`
- `sc_post_id`
- `sc_post_ids`
- `sc_manager_user_id`

## Risk Analysis

- Classification: `PASS`
- This was a high-risk governed ACL/ownership batch, but the final scope stayed
  additive and did not expose platform-governance fields through the enterprise
  user-maintenance page.

## Rollback

- `git restore AGENTS.md`
- `git restore addons/smart_enterprise_base/security/ir.model.access.csv`
- `git restore addons/smart_enterprise_base/views/menu_enterprise_base.xml`
- `git restore addons/smart_construction_custom/tests/test_business_admin_authority_path.py`
- `git restore agent_ops/tasks/ITER-2026-03-31-433.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-433.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-433.json`

## Next Suggestion

- Run one final low-risk governance audit to confirm that the full enterprise
  maintenance chain is now delivery-complete for the customer and no further
  ownership split remains.
