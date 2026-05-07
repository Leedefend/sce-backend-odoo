# Organization Visible Surface Analysis v1

Status: ACCEPTED_FOR_CURRENT_VISIBLE_SURFACE
Date: 2026-05-07

## Scope

Analyze the legacy organization sources and decide what should be visible as
the user's organization structure in the new system.

## Sources

- `BASE_ORGANIZATION_DEPARTMENT`: legacy department/tree facts.
- `BASE_SYSTEM_USER` + `tr_user`: legacy user profile and department reference.
- `BASE_SYSTEM_USER_ROLE` + `tr_RoleToUser`: legacy role assignments and role names.
- Current formal carrier: `hr.department` under one `res.company`
  (`四川保盛建设集团有限公司`).

## Findings

- The legacy department payload contains `828` rows.
- `732` legacy department rows are project-like names containing terms such as
  `工程`, `项目`, `施工`, `改造`, `维修`, `建设`, `总承包`, `分包`, `采购`, `装修`, or `安装`.
- These rows are useful historical facts, but they are not user-visible
  enterprise departments.
- The legacy user profile payload contains `101` rows. `85` rows have a legacy
  department id, but the current acceptance login users are not legacy users, so
  user access is not yet driven by these legacy departments.
- Role names provide stronger formal department hints than most legacy
  department rows: `工程部`, `经营部`, `财务部`, `行政部`, `项目部`, `总经理`,
  and `综合行政部`.
- The acceptance database currently has no legacy profile bound to `res.users`.
  Therefore the historical user menu must not default to "bound new users";
  otherwise the organization-user fact surface appears empty even though replay
  has loaded the historical records.

## Decision

- Keep all legacy rows in `sc.legacy.department`, `sc.legacy.user.profile`, and
  `sc.legacy.user.role` for traceability.
- Materialize only user-visible organization units into `hr.department`.
- Do not create additional `res.company` records for legacy branch/company-like
  rows in this round.
- Do not show project-like legacy department rows in the organization structure.
- Exclude the technical `系统管理` department from the organization action.
- Keep the organization action scoped to the active company. The custom frontend
  must support standard Odoo `allowed_company_ids[0]` expressions in
  `domain_raw` and `context_raw`; this is a platform contract, not a one-off
  organization workaround.

## Acceptance Snapshot

After replaying legacy user context and re-running organization materialization
against `sc_partner_acceptance`:

- `sc.legacy.department`: `830` rows after derived parent/user department facts.
- `hr.department` user-visible action result: `28` rows.
- Root user-visible organization nodes: `四川保盛建设集团有限公司`.
- Duplicate visible department names: `0`.
- Project-like legacy facts remain preserved as inactive/non-visible formal
  departments or only as `sc.legacy.department` facts.
- Browser validation through custom frontend action `682`: PASS. The page shows
  `28 条记录`, includes core departments such as `工程部`, `经营部`, and `总经理`,
  and does not expose `系统管理` or `Administration`.
- Historical user context backend facts are replayed for traceability:
  `sc.legacy.user.profile` has `101` rows including inactive historical users,
  and `sc.legacy.user.role` has `330` rows.

## Next

The next implementation pass should connect selected user accounts to formal
departments only when the user-facing account acceptance scenario requires it.
Legacy project authorization and role facts should remain separate from the
organization tree.
