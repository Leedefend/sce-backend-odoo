# ITER-2026-03-31-416 Report

## Summary

- Froze the governance design for a new `业务系统管理员` authority path.
- Confirmed that ordinary business-role carriers can continue to reuse existing capability and bridge groups.
- Confirmed that the new business-system-admin path must be introduced as a distinct authority path because current top-level carriers imply `base.group_system`.

## Changed Files

- `agent_ops/tasks/ITER-2026-03-31-416.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-416.md`
- `agent_ops/state/task_results/ITER-2026-03-31-416.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-416.yaml` -> PASS

## Design Facts

### 1. Existing ordinary business-role carriers are reusable

Observed in:

- `addons/smart_construction_core/models/support/res_users_role_profile.py`
- `addons/smart_construction_core/security/sc_role_groups.xml`
- `addons/smart_construction_core/tests/perm_matrix.py`

Facts:

- existing product-role carrier:
  - `res.users.sc_role_profile`
- existing capability and bridge groups already cover ordinary business lanes:
  - project
  - contract
  - cost
  - finance
  - material
- these lanes can be composed without necessarily requiring platform admin

Conclusion:

- `通用角色` can continue to align with ordinary internal business-user paths
- no new carrier field is required for that part

### 2. Current top authority carriers are unusable for customer business admin

Observed in:

- `addons/smart_construction_core/models/support/res_users_role_profile.py`
- `addons/smart_construction_core/security/sc_capability_groups.xml`

Facts:

- current top-level role carriers route through:
  - `smart_construction_core.group_sc_cap_config_admin`
  - `smart_construction_core.group_sc_super_admin`
- both eventually imply:
  - `base.group_system`

Conclusion:

- current `executive`
- current `config_admin`
- current `super_admin`

cannot be reused as the customer-defined `业务系统管理员`

### 3. Minimal design boundary for the new authority path

The new path should:

- sit above ordinary business-user roles
- include business configuration authority needed inside the enterprise system
- exclude:
  - `base.group_system`
  - platform-level settings
  - platform-level ops/super-admin semantics

The new path should be additive and isolated:

- new business-admin group path in the customer/business permission lane
- no silent reuse of `group_sc_super_admin`
- no silent reuse of `group_sc_cap_config_admin` if it still implies `base.group_system`

## Minimal Next Implementation Boundary

The next high-risk implementation batch should be limited to:

1. introduce a new customer/business admin authority group path
2. ensure it does not imply `base.group_system`
3. remap workbook `管理员角色` to that new path
4. keep `通用角色` on the existing ordinary internal-user path

That batch will necessarily intersect security semantics and must therefore run
as a dedicated permission-governance batch.

## Risk Analysis

- Classification: `PASS_WITH_RISK`
- Risk reason:
  - the next executable step requires security-domain changes
  - current highest role carriers still violate the frozen customer boundary

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-31-416.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-416.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-416.json`

## Next Suggestion

- Open a dedicated high-risk permission-governance task to add a new business-system-admin authority path that is explicitly separated from `base.group_system`.
