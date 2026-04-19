# Account-Lane Onboarding Screen v1

## Batch

- Task: `ITER-2026-04-18-ACCOUNT-LANE-ONBOARDING-SCREEN`
- Layer Target: Business Fact Screening
- Module: account-lane onboarding classification
- Module Ownership: customer-delivery business continuity
- Kernel or Scenario: scenario
- Backend Sub-Layer: business-fact layer
- Reason: same-person cross-account screening proved that business continuity is
  currently carried by the same people through separate upstream/downstream
  accounts, so the next question is whether the current need is onboarding
  guidance or governance.

## Scope

- Screen only.
- Allowed outputs: this report, task contract, delivery context log.
- No source code changes.
- No frontend model special-cases.
- No payment, settlement, account, ACL, record-rule, or manifest changes.

## Inputs

- `product_entry_openability_screen_v1.md`:
  upstream product maintenance entry is already openable for the upstream owner chain.
- `cross_role_handoff_verify_screen_v1.md`:
  purchase-manager and payment-manager chains do not overlap at account level.
- `same_person_cross_account_handoff_screen_v1.md`:
  all 8 payment-manager examples match same-name legacy purchase-manager accounts.

## Classification

- Current business continuity is best classified as a same-person cross-account
  operating procedure:
  - upstream product/purchase work uses legacy-style purchase-manager accounts
  - downstream settlement/payment work uses current payment-manager accounts
  - the same natural people can complete both sides through different logins
- This means the immediate need is operational guidance and account-lane clarity,
  not business-semantic repair.
- A future account-convergence or permission-governance batch may still be
  justified later, but it is not required to explain the current continuity path
  and should not be confused with a current runtime blocker.

## Decision

- Do not open payment or settlement implementation from this result.
- Do not open a frontend UX workaround batch from this result.
- Do not open a permission-governance batch as the immediate next step.
- The immediate next deliverable should be an onboarding/operating note that
  explains which account lane handles which step for the same person.

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-18-ACCOUNT-LANE-ONBOARDING-SCREEN.yaml`: PASS
- `git diff --check`: PASS

## Risk And Stop Decision

- Result: PASS.
- Stop condition: none in this screen.
- Risk: if users are not told which account lane to use at each step, they may
  still experience operational confusion even though the runtime path exists.
- Boundary: any later account-convergence work should be opened as a separate
  governance objective, not bundled into payment, settlement, or frontend fixes.

## Next Step

Open a low-cost operational-guidance documentation batch:

- write the same-person cross-account upstream/downstream operating note;
- keep payment, settlement, ACL, and frontend code frozen;
- if later the team wants single-account convergence, open that as a separate
  governance/planning line instead of mixing it into the current continuity lane.
