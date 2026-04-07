# Project Member Rule Binding Screen v1

## Purpose
- Prepare the next dedicated permission-binding iteration using project-member
  facts delivered by `ITER-2026-04-07-1275`.

## In-Scope Next Iteration Targets
- `project.project`
- `project.task`
- `project.budget`
- `project.cost.ledger`
- `payment.request`
- `payment.ledger`
- `sc.settlement.order`

## Candidate Authority Artifacts
- `addons/smart_construction_core/security/sc_record_rules.xml`
- `addons/smart_construction_core/security/ir.model.access.csv` (only if strictly required)

## Binding Principle
- Use project-member facts as primary access truth:
  - key role fields on `project.project`
  - `project_member_ids` carrier (`project.responsibility`)
- Keep company/project anchors as mandatory precondition.
- Apply additive, minimal, object-scoped rule deltas.

## Proposed Execution Order
1. Implement `project.project` + `project.task` minimal member-bound visibility rules.
2. Implement `project.budget` + `project.cost.ledger` member-bound visibility rules.
3. Implement `payment.request` + `payment.ledger` + `sc.settlement.order` member-bound visibility rules.
4. Run real-role operability verifies for owner/pm/finance.

## Verify Checklist (Next Iteration)
- Non-member same-company user cannot see unrelated project records.
- Project manager/member can access own project/task.
- Budget/cost/payment/settlement follow project-member boundaries.
- Stage gate and real-role smoke remain pass.

## Stop/Guard Notes
- This screen batch does not modify ACL/record-rule files.
- Implementation must run in dedicated high-risk task line with explicit allowlist.
