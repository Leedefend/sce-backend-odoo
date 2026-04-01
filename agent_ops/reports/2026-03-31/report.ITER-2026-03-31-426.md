# ITER-2026-03-31-426 Report

## Summary

- Extended the platform post carrier from one primary post to one primary post
  plus additive extra posts.
- Added an extra-post bootstrap path for the previously deferred workbook
  semantics.
- Attached deferred extra posts to live customer users in `sc_demo`.

## Changed Files

- `addons/smart_enterprise_base/models/res_users.py`
- `addons/smart_enterprise_base/models/sc_enterprise_post.py`
- `addons/smart_enterprise_base/views/res_users_views.xml`
- `addons/smart_construction_custom/models/security_policy.py`
- `addons/smart_construction_custom/data/security_policy_actions.xml`
- `addons/smart_construction_custom/tests/test_business_admin_authority_path.py`
- `agent_ops/tasks/ITER-2026-03-31-426.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-426.md`
- `agent_ops/state/task_results/ITER-2026-03-31-426.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-426.yaml` -> PASS
- `python3 -m py_compile addons/smart_enterprise_base/models/res_users.py addons/smart_enterprise_base/models/sc_enterprise_post.py addons/smart_construction_custom/models/security_policy.py addons/smart_construction_custom/tests/test_business_admin_authority_path.py` -> PASS
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_enterprise_base DB_NAME=sc_demo` -> PASS
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_custom DB_NAME=sc_demo` -> PASS
- `docker exec -i sc-backend-odoo-dev-odoo-1 odoo shell -d sc_demo ... bootstrap_customer_user_extra_posts()` -> PASS
- `make verify.smart_core` -> PASS

## Runtime Result

- updated extra-post users: `3`
- created extra-post rows: `1`
- unresolved users: none
- verified samples:
  - `wennan.extra_posts` contains `副总经理`
  - `hujun.extra_posts` contains `总经理`

## Outcome

The customer workbook multi-post semantics now have a repository-backed carrier:

- primary post: `res.users.sc_post_id`
- extra posts: `res.users.sc_post_ids`

This closes the previously deferred workbook extra-post subset without changing:

- ACL scope
- record rules
- manifest

## Risk Analysis

- Classification: `PASS`
- The earlier failed upgrade attempt was caused by concurrent module upgrades,
  not by implementation defects; rerunning upgrades serially resolved the issue.
- Extra-post writes remained additive and company-scoped.

## Rollback

- `git restore addons/smart_enterprise_base/models/res_users.py`
- `git restore addons/smart_enterprise_base/models/sc_enterprise_post.py`
- `git restore addons/smart_enterprise_base/views/res_users_views.xml`
- `git restore addons/smart_construction_custom/models/security_policy.py`
- `git restore addons/smart_construction_custom/data/security_policy_actions.xml`
- `git restore addons/smart_construction_custom/tests/test_business_admin_authority_path.py`
- `git restore agent_ops/tasks/ITER-2026-03-31-426.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-426.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-426.json`

## Next Suggestion

- Continue with customer bootstrap completion by deciding whether workbook
  `extra_departments` should remain governance-only or move to a future
  multi-department platform extension.
