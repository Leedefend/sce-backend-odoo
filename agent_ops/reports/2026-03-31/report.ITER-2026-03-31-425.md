# ITER-2026-03-31-425 Report

## Summary

- Implemented additive customer primary-post bootstrap for the frozen 12-user
  workbook mapping.
- Created missing customer post master-data rows idempotently.
- Attached workbook primary posts to `res.users.sc_post_id`.

## Changed Files

- `addons/smart_construction_custom/models/security_policy.py`
- `addons/smart_construction_custom/data/security_policy_actions.xml`
- `addons/smart_construction_custom/tests/test_business_admin_authority_path.py`
- `agent_ops/tasks/ITER-2026-03-31-425.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-425.md`
- `agent_ops/state/task_results/ITER-2026-03-31-425.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-425.yaml` -> PASS
- `python3 -m py_compile addons/smart_construction_custom/models/security_policy.py addons/smart_construction_custom/tests/test_business_admin_authority_path.py` -> PASS
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_custom DB_NAME=sc_demo` -> PASS
- `docker exec -i sc-backend-odoo-dev-odoo-1 odoo shell -d sc_demo ... bootstrap_customer_user_primary_posts()` -> PASS
- `make verify.smart_core` -> PASS

## Runtime Result

- updated post users: `12`
- created post rows: `6`
- unresolved users: none
- verified samples:
  - `wennan` -> `财务经理`
  - `wutao` -> `董事长`

## Outcome

The customer workbook post baseline is now executable in `sc_demo`.

The repository now has an additive bootstrap entrypoint that can:

- create missing `sc.enterprise.post` rows for the customer company
- attach one primary post to each resolved user
- preserve extra posts only as deferred semantics

## Risk Analysis

- Classification: `PASS`
- No unresolved workbook post members remained.
- Post writes stayed additive and only targeted the new `sc_post_id` carrier.
- No extra-post persistence was introduced implicitly.

## Rollback

- `git restore addons/smart_construction_custom/models/security_policy.py`
- `git restore addons/smart_construction_custom/data/security_policy_actions.xml`
- `git restore addons/smart_construction_custom/tests/test_business_admin_authority_path.py`
- `git restore agent_ops/tasks/ITER-2026-03-31-425.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-425.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-425.json`

## Next Suggestion

- Continue with the customer bootstrap line and decide whether deferred
  extra-post semantics should stay in governance only or receive a future
  multi-post platform extension.
