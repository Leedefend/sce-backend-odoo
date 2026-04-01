# ITER-2026-03-31-422 Report

## Summary

- Implemented a platform-level `岗位` master-data carrier in
  `smart_enterprise_base`.
- Added one primary post field on `res.users`.
- Added admin-only post maintenance views, action, menu, and the exact ACL
  entry needed for the new model.

## Changed Files

- `addons/smart_enterprise_base/models/__init__.py`
- `addons/smart_enterprise_base/models/res_users.py`
- `addons/smart_enterprise_base/models/sc_enterprise_post.py`
- `addons/smart_enterprise_base/views/res_users_views.xml`
- `addons/smart_enterprise_base/views/menu_enterprise_base.xml`
- `addons/smart_enterprise_base/security/ir.model.access.csv`
- `agent_ops/tasks/ITER-2026-03-31-422.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-422.md`
- `agent_ops/state/task_results/ITER-2026-03-31-422.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-422.yaml` -> PASS
- `python3 -m py_compile addons/smart_enterprise_base/models/res_users.py addons/smart_enterprise_base/models/sc_enterprise_post.py` -> PASS
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_enterprise_base DB_NAME=sc_demo` -> PASS
- `docker exec -i sc-backend-odoo-dev-odoo-1 odoo shell -d sc_demo ...` -> PASS
- `make verify.smart_core` -> PASS

## Runtime Result

Verified in `sc_demo`:

- `sc.enterprise.post` model exists
- `res.users.sc_post_id` field exists
- `smart_enterprise_base.action_enterprise_post` exists
- `smart_enterprise_base.menu_enterprise_post` exists

## Implementation Notes

The new carrier is intentionally narrow:

- one primary post only
- post master data remains separate from departments
- post master data remains separate from workbook system roles and permission
  groups
- ACL scope is limited to `base.group_system` for the new post model

## Outcome

The repository now has a real platform-backed target for workbook `岗位`.

Customer bootstrap can continue later without overloading:

- departments
- direct manager relations
- business system roles

## Risk Analysis

- Classification: `PASS`
- ACL change stayed inside the single approved file and remained additive.
- No record rules, manifest changes, or financial domains were touched.
- Existing non-blocking warnings during module upgrade remained unchanged from
  prior runs and did not block the batch.

## Rollback

- `git restore addons/smart_enterprise_base/models/__init__.py`
- `git restore addons/smart_enterprise_base/models/res_users.py`
- `git restore addons/smart_enterprise_base/models/sc_enterprise_post.py`
- `git restore addons/smart_enterprise_base/views/res_users_views.xml`
- `git restore addons/smart_enterprise_base/views/menu_enterprise_base.xml`
- `git restore addons/smart_enterprise_base/security/ir.model.access.csv`
- `git restore agent_ops/tasks/ITER-2026-03-31-422.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-422.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-422.json`

## Next Suggestion

- Continue with the customer bootstrap line and attach workbook `岗位` values to
  the new `res.users.sc_post_id` carrier using the frozen primary-post rule.
