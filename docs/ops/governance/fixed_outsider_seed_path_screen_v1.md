# Fixed Outsider Seed Path Screen v1

## Objective
- Enable strict fixed-user outsider deny matrix verification in a reproducible
  way by introducing one stable outsider identity in customer seed lane.

## Proposed Path
1. Add one outsider user in `smart_construction_custom` seed data.
2. Keep outsider in same company, base employee group only.
3. Exclude outsider from project/cost/finance/settlement capability groups.
4. Keep password aligned with acceptance env convention (`demo`).

## Candidate Implementation Scope
- `addons/smart_construction_custom/data/customer_users.xml`
- `addons/smart_construction_custom/data/customer_user_authorization.xml`
- (if needed) related seed documentation path only.

## Guardrails
- Do not touch ACL/record-rule files in this seed batch.
- Do not alter existing role-bearing users.
- Additive seed only.

## Verification Plan (Next Batch)
- Re-run fixed-user matrix verify with explicit outsider login.
- Assert outsider deny on:
  - `project.project`
  - `project.task`
  - `project.budget`
  - `project.cost.ledger`
  - `payment.request`
  - `sc.settlement.order`
