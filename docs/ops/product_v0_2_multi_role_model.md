# Product v0.2 Multi-Role Model

## Purpose
- Define the role and behavior boundary for v0.2 expansion.
- This phase does not implement a permission system.

## Why v0.2 Needs This
- v0.1 first pilot stayed under a controlled single-operator model.
- Existing repository evidence already shows role surfaces and payment-request action handoff semantics.
- v0.2 needs a stable product role model before broader trial expansion.

## Source Evidence
- `addons/smart_construction_core/core_extension.py`
  - role landing scenes and menu surfaces already distinguish `owner`, `pm`, `finance`, `executive`
- `addons/smart_construction_core/tests/test_payment_request_available_actions_backend.py`
  - payment actions already carry `required_role_key`, `required_role_label`, and handoff hints

## Proposed Product Roles
- `project_operator`
  - primary owner of project initiation, planning, and execution progression
  - current closest role: `pm`
- `project_sponsor`
  - business owner for scope/result review
  - current closest role: `owner`
- `finance_operator`
  - handles payment request preparation and finance-side action execution
  - current closest role: `finance`
- `decision_owner`
  - handles exception approval, rejection, and executive escalation
  - current closest role: `executive`

## Recommended Role Boundary
- `project_operator`
  - may initiate project flow
  - may manage execution queue/focus task
  - may respond to pilot precheck and execution blockers
- `project_sponsor`
  - may review project status and confirm business context
  - should not become the default execution actor
- `finance_operator`
  - may receive handoff from project-side flow
  - owns finance-side action completion and document completeness
- `decision_owner`
  - resolves exception and policy decisions
  - should act as escalation role, not default operator

## Behavior Model
- Role design should answer:
  - who sees the next action
  - who may execute the next action
  - who must hand off when role mismatch occurs
  - who owns blocked-state resolution

## Product Constraints
- Role model must be product-semantic first, ACL-second.
- Do not equate every Odoo group directly to a product role.
- One user may carry multiple groups, but the product should still show one current acting role per flow.
- Handoff hints must remain explicit in the action surface.

## v0.2 Recommended Pattern
- Introduce `acting_role` as product context, not as a hard permission implementation in this phase.
- Keep role handoff explicit on action payloads.
- Expand only the minimum role set needed for the chosen second business chain.

## Non-Goals
- no ACL matrix implementation
- no record-rule implementation
- no automatic role switching behavior
- no cross-module permission redesign
