# ITER-2026-03-31-400 Report

## Summary

- Audited `smart_construction_custom` by boundary ownership rather than by
  coding style.
- Confirmed that the module is not a business-fact extension module.
- Confirmed that it currently mixes three distinct responsibilities:
  - role / permission governance
  - ACL attachment to core business models
  - demo-user bootstrap / policy application glue

## Changed Files

- `agent_ops/tasks/ITER-2026-03-31-400.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-400.md`
- `agent_ops/state/task_results/ITER-2026-03-31-400.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-400.yaml` -> PASS

## Evidence

Module declaration:

- [__manifest__.py](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/__manifest__.py#L10)
- [__manifest__.py](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/__manifest__.py#L13)
- [__manifest__.py](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/__manifest__.py#L18)

Observed facts:

- depends only on `smart_construction_core`
- loads only:
  - role groups
  - ACL
  - server actions
- has a `post_init_hook`

Hook glue:

- [hooks.py](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/hooks.py#L2)
- [hooks.py](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/hooks.py#L6)

Policy service:

- [security_policy.py](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/models/security_policy.py#L5)
- [security_policy.py](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/models/security_policy.py#L10)
- [security_policy.py](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/models/security_policy.py#L38)
- [security_policy.py](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/models/security_policy.py#L64)

Role groups:

- [role_matrix_groups.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/security/role_matrix_groups.xml#L4)
- [role_matrix_groups.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/security/role_matrix_groups.xml#L22)
- [role_matrix_groups.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/security/role_matrix_groups.xml#L40)
- [role_matrix_groups.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/security/role_matrix_groups.xml#L58)
- [role_matrix_groups.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/security/role_matrix_groups.xml#L82)
- [role_matrix_groups.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/security/role_matrix_groups.xml#L91)
- [role_matrix_groups.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/security/role_matrix_groups.xml#L101)
- [role_matrix_groups.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/security/role_matrix_groups.xml#L110)

ACL:

- [ir.model.access.csv](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/security/ir.model.access.csv#L2)
- [ir.model.access.csv](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/security/ir.model.access.csv#L3)
- [ir.model.access.csv](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/security/ir.model.access.csv#L9)
- [ir.model.access.csv](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/security/ir.model.access.csv#L15)

Server actions:

- [security_policy_actions.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/data/security_policy_actions.xml#L4)
- [security_policy_actions.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/data/security_policy_actions.xml#L10)

## Ownership Classification

### 1. Role matrix groups

Files:

- `security/role_matrix_groups.xml`

Classification:

- `belongs_to = role / permission governance`

Reason:

- these records define user-role groupings and their implied capability groups
- they do not define industry business facts
- they do not define scene or frontend behavior

Boundary conclusion:

- this content should live in a dedicated role-governance boundary, not in a
  general “custom business fact” bucket

### 2. ACL rows for core business models

Files:

- `security/ir.model.access.csv`

Classification:

- `belongs_to = permission governance`

Reason:

- the file grants read/write/create/delete rights to core business models
- it directly governs contract / settlement / payment access
- this is the highest-risk part of the module under repository rules

Boundary conclusion:

- this content should remain governed as security policy, not be treated as a
  lightweight customization layer

### 3. Policy hook and policy transient model

Files:

- `hooks.py`
- `models/security_policy.py`
- `data/security_policy_actions.xml`

Classification:

- split ownership:
  - `apply_business_full_policy` -> role / permission bootstrap
  - `apply_role_matrix` -> mixed role bootstrap + demo-user bootstrap
  - server actions -> admin/governance operations

Reason:

- `apply_business_full_policy` mutates implied groups on a core capability group
- `apply_role_matrix` both links role groups to capability groups and assigns
  demo users by login
- these are not business facts; they are governance/bootstrap glue

Boundary conclusion:

- policy glue should be split conceptually into:
  - role-governance bootstrap
  - demo-user/bootstrap mapping
  - optional admin action surface

### 4. Demo user mapping

Evidence:

- [security_policy.py](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/models/security_policy.py#L64)
- [security_policy.py](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/models/security_policy.py#L105)

Classification:

- `belongs_to = demo/bootstrap`

Reason:

- explicit logins such as `demo_role_pm`, `demo_role_finance`, and
  `demo_role_executive` are environment/bootstrap concerns, not reusable role
  governance primitives

Boundary conclusion:

- this content should not stay coupled to the same unit as reusable role
  governance if the module is to match the intended boundaries

## Main Conclusion

`smart_construction_custom` currently mixes three responsibilities that should
not be treated as one homogeneous “industry customization” concern:

- reusable role/permission governance
- ACL attachment to core business models
- demo user bootstrap

So the right next step is not an ungoverned cleanup pass inside the module.
The right next step is a governed split objective that explicitly decides:

1. what remains as reusable role governance
2. what remains as security/ACL policy
3. what moves to demo/bootstrap ownership

## What Fits The Designed Boundaries

Can be justified as role-governance content:

- role group definitions
- implied capability mappings
- optional admin policy actions

Should not be described as business-fact content:

- ACL rows on core business models
- demo login-to-group assignment
- post-init user/group mutation glue

## Risk Analysis

- Risk remained low because this batch was audit-only.
- No security or ACL files were modified.
- A direct implementation cleanup was intentionally deferred because repository
  stop rules explicitly treat these paths as high-risk.

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-31-400.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-400.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-400.json`

## Next Suggestion

- Open a governed high-risk objective for `smart_construction_custom` with three
  explicit batches:
  1. freeze reusable role-governance records
  2. isolate demo-user bootstrap out of policy glue
  3. review whether ACL rows should remain here or move to a dedicated security
     governance module
