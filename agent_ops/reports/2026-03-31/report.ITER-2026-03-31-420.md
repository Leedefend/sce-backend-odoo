# ITER-2026-03-31-420 Report

## Summary

- Implemented additive customer user `system_roles` bootstrap for the frozen
  14-user workbook mapping.
- Attached workbook `管理员角色` to
  `smart_construction_custom.group_sc_role_business_admin`.
- Attached workbook `通用角色` to
  `smart_construction_custom.group_sc_role_owner`.

## Changed Files

- `addons/smart_construction_custom/models/security_policy.py`
- `addons/smart_construction_custom/data/security_policy_actions.xml`
- `addons/smart_construction_custom/tests/test_business_admin_authority_path.py`
- `agent_ops/tasks/ITER-2026-03-31-420.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-420.md`
- `agent_ops/state/task_results/ITER-2026-03-31-420.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-420.yaml` -> PASS
- `python3 -m py_compile addons/smart_construction_custom/models/security_policy.py addons/smart_construction_custom/tests/test_business_admin_authority_path.py` -> PASS
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_custom DB_NAME=sc_demo` -> PASS
- `docker exec sc-odoo-web-1 odoo shell -d sc_demo ... bootstrap_customer_user_system_roles()` -> PASS
- `make verify.smart_core` -> PASS

## Runtime Result

- workbook role users attached: `14`
- unresolved users: none
- `管理员角色` attached users:
  - `duanyijun`
  - `wennan`
  - `admin`
  - `shuiwujingbanren`
- `通用角色` attached users:
  - `wutao`
  - `yangdesheng`
  - `xudan`
  - `chentianyou`
  - `wennan`
  - `lilinxu`
  - `yinjiamei`
  - `admin`
  - `zhangwencui`
  - `chenshuai`
  - `xiaohuijiu`
  - `hujun`

## Outcome

The customer workbook role baseline is now executable in `sc_demo`.

The repository now has an additive bootstrap entrypoint that can:

- resolve workbook system-role labels by login
- attach the new business-system-admin authority path
- attach the ordinary internal business-user path
- leave unresolved users empty under the frozen baseline

## Risk Analysis

- Classification: `PASS`
- No unresolved workbook role members remained.
- Group writes stayed additive.
- Some admin-tagged users can still appear with both role groups in live
  snapshots because the workbook itself contains dual labels for some users and
  existing group state is preserved additively; this batch did not require
  destructive normalization.

## Rollback

- `git restore addons/smart_construction_custom/models/security_policy.py`
- `git restore addons/smart_construction_custom/data/security_policy_actions.xml`
- `git restore addons/smart_construction_custom/tests/test_business_admin_authority_path.py`
- `git restore agent_ops/tasks/ITER-2026-03-31-420.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-420.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-420.json`

## Next Suggestion

- Continue with the platform-level post/master-data extension line so workbook
  `岗位` can move from deferred semantics into a real repository-backed user
  field.
