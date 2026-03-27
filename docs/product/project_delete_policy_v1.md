# Project Delete Policy v1

- Date: `2026-03-27`
- Status: `Frozen`
- Scope: `project.project`
- Strategy: `默认归档，禁止普通物理删除`

## Position

`project.project` is the business aggregate root of the construction system.

It is not ordinary master data. It carries or anchors:

- budget
- cost
- payment
- settlement
- boq
- material plan
- risk
- evidence exception
- treasury ledger
- reporting projections

Therefore, project deletion must be treated as a governed destruction policy, not a list-page convenience action.

## Current Risk Assessment

Current code paths do not provide one unified delete semantic.

- Some related data uses `ondelete="cascade"` and will be physically removed.
- Some related data uses required foreign keys without an explicit `ondelete`, which will usually block deletion.
- Some read models are SQL views and will disappear indirectly after source data changes.

This means direct physical deletion of a project is currently non-deterministic from a product perspective.

## Frozen Rule

From v1 onward:

- `project.project` must not be exposed as a normal physical delete target in the custom frontend.
- Standard list pages must use archive/close semantics for projects.
- `api.data.unlink` must not allow `project.project`.
- Physical deletion of a project is not a user-facing batch action.

## Allowed User Action

For ordinary product flows, users may only:

- archive a project
- close a project
- remove draft sub-records under controlled business rules

They may not directly hard-delete a project from the project list.

## Future Destruction Gate

If physical deletion is needed in the future, it must be implemented as a dedicated governed flow with:

1. dependency scan
2. impact report
3. blocking reasons
4. explicit destroy eligibility
5. auditable operator confirmation

## Minimum Eligibility For Future Hard Delete

At minimum, all of the following must be true:

- project is test/demo/sandbox scoped, or explicitly marked destroyable
- no active budget/cost/payment/settlement/material/risk/evidence data remains
- no immutable audit/evidence policy is violated
- system produces a destruction preview before execution

## Immediate Product Decision

The current product iteration must prioritize:

- safe archive behavior
- clear user messaging
- no accidental destruction entry

instead of enabling project hard delete.
