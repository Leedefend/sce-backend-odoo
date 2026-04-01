# ITER-2026-03-31-407 Report

## Summary

- Translated the confirmed customer baseline into a system mapping draft.
- Split the mapping into five layers:
  - enterprise
  - organization
  - post attributes
  - system roles
  - customer bootstrap
- Clarified what should later be implemented in `smart_construction_custom`
  versus what should remain outside it.

## Changed Files

- `agent_ops/tasks/ITER-2026-03-31-407.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-407.md`
- `agent_ops/state/task_results/ITER-2026-03-31-407.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-407.yaml` -> PASS

## Mapping Draft

### 1. Enterprise layer

System target:

- company / enterprise master

Current mapping:

- enterprise_name -> `四川保盛建设集团有限公司`

Recommended system handling:

- create one active customer company record
- use this company as the root owner for department, user, and later project
  mapping

### 2. Organization layer

System target:

- department tree

Frozen formal departments:

- `经营部`
- `工程部`
- `财务部`
- `行政部`
- `成控部`
- `项目部`

Recommended system handling:

- create these as first-level departments under the company root
- do not import `公司员工` as a department

Special rule for `项目部`:

- keep as a real department node
- allow users to belong only to `项目部`
- preserve later extension room for project-linked independent accounting or
  project-side ownership

### 3. Post attribute layer

System target:

- user post / job-title attributes

Frozen posts:

- `董事长`
- `总经理`
- `副总经理`
- `项目负责人`
- `临时项目负责人`
- `财务经理`
- `财务助理`

Recommended system handling:

- do not model these as departments
- store them as user-side post attributes or user profile metadata
- normalize `董事长1` to `董事长`

### 4. System role layer

System target:

- permission / group assignment

Frozen system roles:

- `管理员角色`
- `通用角色`

Recommended system handling:

- keep these in the role/governance layer, not in enterprise post data
- later map them into `smart_construction_custom` role groups / implied groups

### 5. Customer bootstrap layer

System target:

- installation/bootstrap semantics inside `smart_construction_custom`

Recommended bootstrap responsibilities:

- assign users to the frozen company
- assign users to the confirmed departments
- attach post metadata
- attach system roles
- preserve accepted special cases:
  - multi-department users
  - `项目部 only` users
  - role-only users

This means the later bootstrap logic should not “fix” those users away; it
should preserve them as valid customer structure.

## Recommended Customer Import Shape

The later implementation/import batch should aim to produce four practical
tables:

### A. Company table

- company_name

### B. Department table

- department_name
- parent_department
- company_name
- notes

### C. User table

- login
- display_name
- mobile
- company_name
- primary_department
- extra_departments
- post
- system_roles
- status

### D. Exception bucket table

- user
- exception_type
  - `multi_department`
  - `project_department_only`
  - `role_only`
- accepted_by_owner = `true`
- notes

## What Should Later Be Implemented In smart_construction_custom

Suitable future implementation content:

- customer role-governance group mapping
- customer bootstrap rules for department/user/role assignment
- customer-specific accepted exception handling

Not suitable to force into this module as business facts:

- general industry models
- scene/page/frontend semantics
- workbook-as-source logic

## Main Conclusion

The customer data now has an implementation-ready system mapping draft.

The next implementation objective can start from:

- company creation semantics
- department tree bootstrap semantics
- user-to-department and user-to-role bootstrap semantics

without reopening workbook interpretation.

## Risk Analysis

- Risk remained low because this batch was governance-only.
- No addon implementation or security files were changed.
- The remaining work is now implementation planning, not source-data analysis.

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-31-407.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-407.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-407.json`

## Next Suggestion

- Open the first implementation batch for customer bootstrap semantics.
- Lowest-risk first target:
  - company + department bootstrap draft
  - user assignment draft
  - role attachment draft
