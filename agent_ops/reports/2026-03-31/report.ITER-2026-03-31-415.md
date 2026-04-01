# ITER-2026-03-31-415 Report

## Summary

- Audited whether existing repository role carriers can satisfy the newly frozen customer rule for `管理员角色` and `通用角色`.
- Confirmed that `通用角色` can reuse the existing product-role carrier path.
- Confirmed that `管理员角色` cannot directly reuse the existing highest-role carriers without violating the boundary against platform-level authority.

## Changed Files

- `agent_ops/tasks/ITER-2026-03-31-415.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-415.md`
- `agent_ops/state/task_results/ITER-2026-03-31-415.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-415.yaml` -> PASS

## Repository Facts

### 1. The repository already has a formal product-role carrier

Observed in:

- `addons/smart_construction_core/models/support/res_users_role_profile.py`

Facts:

- current role carrier field:
  - `res.users.sc_role_profile`
- current supported values:
  - `owner`
  - `pm`
  - `finance`
  - `executive`

Conclusion:

- workbook-origin system roles do not need a brand-new user-role carrier field
- they can, in principle, map into the existing product-role carrier layer

### 2. `通用角色` can fit the existing non-admin carrier path

Observed in:

- `addons/smart_construction_core/models/support/res_users_role_profile.py`

Facts:

- `owner` already maps to:
  - `smart_construction_custom.group_sc_role_owner`
  - `smart_construction_core.group_sc_cap_project_read`
- this path does not rely on `base.group_system`

Conclusion:

- `通用角色` can safely map to an ordinary internal business-user role path
- current repository facts support this direction

### 3. `管理员角色` conflicts with the current highest-role carriers

Observed in:

- `addons/smart_construction_core/models/support/res_users_role_profile.py`
- `addons/smart_construction_core/security/sc_capability_groups.xml`

Facts:

- current `executive` role-profile mapping includes:
  - `smart_construction_custom.group_sc_role_executive`
  - `smart_construction_core.group_sc_super_admin`
  - `smart_construction_core.group_sc_cap_config_admin`
- `group_sc_cap_config_admin` implies:
  - `base.group_system`
- `group_sc_super_admin` also implies:
  - `base.group_system`

Conclusion:

- current `executive` does not satisfy the newly frozen customer definition
- current `config admin` and `super admin` paths are platform-level, not business-system-only

### 4. Current repository groups are therefore insufficient without governance change

Facts:

- the customer-defined `管理员角色` means:
  - highest authority inside the enterprise business system
  - must not imply platform-level settings
- repository-backed highest authority currently routes through groups that imply:
  - `base.group_system`

Conclusion:

- workbook `管理员角色` cannot be faithfully mapped today without a permission-governance refactor
- this is not a documentation-only issue; it changes the meaning of the existing security lattice

## Outcome

- `通用角色`: repository-compatible direction exists
- `管理员角色`: repository-compatible direction does not exist yet

This means the customer bootstrap chain cannot continue into direct role
attachment for `管理员角色` under the current low-risk iteration lane.

## Risk Analysis

- Classification: `PASS_WITH_RISK`
- Risk reason:
  - `existing_role_profile_implies_platform_admin`
  - `workbook_role_mapping_requires_security_refactor`

The next implementation step would require touching role-group/security meaning,
which is outside the current low-risk lane and directly intersects the guarded
permission domain.

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-31-415.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-415.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-415.json`

## Next Suggestion

- Stop the current bootstrap implementation chain here.
- Open a dedicated permission-governance batch to create a new business-system-admin authority path that:
  - is higher than ordinary internal business roles
  - does not imply `base.group_system`
  - can then be mapped from workbook `管理员角色`
