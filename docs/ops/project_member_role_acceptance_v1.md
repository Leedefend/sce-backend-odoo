# Project Member Role Acceptance v1

## Acceptance Target
- Admin can create project and configure key positions + project members in native form.
- Project manager/member can see project/task based on project member facts.
- Project responsibilities are no longer only global role statements.

## Pre-Conditions
- Module upgraded on target DB.
- Real role users available (`owner/pm/finance/...`).

## Checklist

### A. Admin Configuration Flow
- Create project in native `project.project` form.
- Fill key positions:
  - project manager
  - technical lead
  - business lead
  - cost lead
  - finance contact
- Add rows in `项目成员配置` with:
  - project role code
  - user
  - department/post
  - primary flag
  - active + effective dates

Expected:
- Save succeeds.
- Member rows persist.
- Project key role fields persist as project-level facts and are not blocked by
  global alias-field coupling.

### B. Project/Task Visibility
- Login as project manager/member.
- Open project list/task list.

Expected:
- Project visible when user is in project members or key positions.
- Task visible through project member linkage and task assignee linkage.

### C. Business Carrying Readiness
- Confirm project member facts exist before budget/cost/payment/settlement operations.

Expected:
- Project organization facts are ready as upstream truth.

## Gate Judgment
- PASS when A/B/C all pass.
- FAIL when any of the following occurs:
  - native form cannot maintain members
  - member facts not reflected in visibility
  - key positions cannot be persisted

## Deferred Scope
- This round does not modify ACL/record-rule files.
- Next iteration will bind access rules to project-member facts as a dedicated
  permission closure task line.
