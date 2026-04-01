# ITER-2026-03-31-417 Report

## Summary

- Implemented a dedicated business-system-admin authority path.
- Reduced `group_sc_cap_config_admin` to enterprise business-system configuration authority only.
- Added a customer-facing `角色-业务系统管理员` group and froze workbook system-role mapping for:
  - `管理员角色`
  - `通用角色`

## Changed Files

- `addons/smart_construction_core/security/sc_capability_groups.xml`
- `addons/smart_construction_custom/security/role_matrix_groups.xml`
- `addons/smart_construction_custom/models/security_policy.py`
- `addons/smart_construction_custom/README.md`
- `addons/smart_construction_custom/tests/__init__.py`
- `addons/smart_construction_custom/tests/test_business_admin_authority_path.py`
- `agent_ops/tasks/ITER-2026-03-31-417.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-417.md`
- `agent_ops/state/task_results/ITER-2026-03-31-417.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-417.yaml` -> PASS
- `python3 -m py_compile addons/smart_construction_custom/models/security_policy.py addons/smart_construction_custom/tests/test_business_admin_authority_path.py` -> PASS
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_demo` -> PASS
- runtime Odoo-shell assertion in `sc_demo` -> PASS
- `make verify.smart_core` -> PASS

## Implementation Outcome

### 1. Business-system config admin no longer implies platform admin

Updated:

- `smart_construction_core.group_sc_cap_config_admin`

Result:

- it now implies only:
  - `smart_construction_core.group_sc_internal_user`
- it no longer implies:
  - `base.group_system`

### 2. New customer-facing business admin group added

Added:

- `smart_construction_custom.group_sc_role_business_admin`

Result:

- it implies:
  - `smart_construction_core.group_sc_business_full`
- it does not directly imply:
  - `base.group_system`

### 3. Workbook role mapping is now explicit in code

Added in `sc.security.policy`:

- `管理员角色` -> `smart_construction_custom.group_sc_role_business_admin`
- `通用角色` -> `smart_construction_custom.group_sc_role_owner`

This gives the customer bootstrap chain a concrete, repository-backed role
attachment target for later additive batches.

## Runtime Evidence

Observed through direct Odoo shell audit in `sc_demo`:

- `config_admin_implied`:
  - `smart_construction_core.group_sc_internal_user`
- `business_admin_implied`:
  - `smart_construction_core.group_sc_business_full`
- `role_mapping`:
  - `管理员角色` -> `group_sc_role_business_admin`
  - `通用角色` -> `group_sc_role_owner`

## Risk Analysis

- Classification: `PASS`
- This remained a high-risk batch, but it completed with clear evidence and
  passing verification.
- Guardrail respected:
  - no `record_rules/**` change
  - no `ir.model.access.csv` change
  - no `__manifest__.py` change
  - no financial-domain change

Non-blocking note:

- module upgrade still emits the existing README/docutils indentation warning in
  `smart_construction_custom`
- it did not block security data loading or runtime verification

## Rollback

- `git restore addons/smart_construction_core/security/sc_capability_groups.xml`
- `git restore addons/smart_construction_custom/security/role_matrix_groups.xml`
- `git restore addons/smart_construction_custom/models/security_policy.py`
- `git restore addons/smart_construction_custom/README.md`
- `git restore addons/smart_construction_custom/tests/__init__.py`
- `git restore addons/smart_construction_custom/tests/test_business_admin_authority_path.py`
- `git restore agent_ops/tasks/ITER-2026-03-31-417.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-417.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-417.json`

## Next Suggestion

- Resume the customer bootstrap chain with the next additive batch:
  - attach workbook `system_roles` to users using the new explicit mapping
- Keep `posts` on a separate platform-master-data extension line.
