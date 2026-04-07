# Project Member Role Design v1

## Goal
- Make `project.project` a real business organization unit after creation.
- Carry project-level key positions and active member roster as business facts.

## Scope
- Native business-fact layer only.
- No frontend contract customization.
- No platform abstraction changes.

## Fact Model

### Project Key Position Fields
- `project_manager_user_id`
- `technical_lead_user_id`
- `business_lead_user_id`
- `cost_lead_user_id`
- `finance_contact_user_id`

These are stored on `project.project` and represent project-internal role carriers.
In this iteration they are constrained as independent business-fact fields (not
`related` aliases), so project role assignment can be maintained at project
scope instead of depending on global user-role aliases.

### Project Member Carrier
- Reuse existing `project.responsibility` as project member factual carrier.
- Add fields:
  - `project_role_code` (alias to `role_key`)
  - `department_id`
  - `post_id`
  - `is_primary`
  - `active`
  - `date_start`
  - `date_end`
  - `note`

## Native UI Entry
- Project form provides member maintenance directly on `project.project`.
- Entry field: `project_member_ids` (alias to `project.responsibility`).
- Members can be added/edited after project creation.

## Minimal Visibility Linkage
- Keep existing record-rule baseline (owner/follower/assignee model).
- Build member facts into project followers via server-side sync:
  - creator
  - project responsible users
  - key position users
  - users matched by member `post_id`

This ensures project/task visibility can consume project-member facts without touching contract/frontend layers.

## Extensibility Base
- Budget/cost/payment/settlement visibility already references project member/follower semantics through project linkage.
- New member facts become shared truth for further business rules.

## Next Iteration Note
- This v1 iteration focuses on fact modeling closure only.
- ACL/record-rule binding is intentionally deferred and will be introduced in the
  next dedicated governance/permission iteration based on these member facts.
