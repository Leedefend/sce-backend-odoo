# Cross-Role Handoff Verify Screen v1

## Batch

- Task: `ITER-2026-04-18-CROSS-ROLE-HANDOFF-VERIFY-SCREEN`
- Layer Target: Business Fact Screening
- Module: cross-role handoff verification
- Module Ownership: customer-delivery business continuity
- Kernel or Scenario: scenario
- Backend Sub-Layer: business-fact layer
- Reason: native upstream product entry is proven; the remaining question is
  whether upstream and downstream runtime owners overlap or require explicit
  cross-role handoff.

## Scope

- Screen only.
- Allowed outputs: this report, task contract, delivery context log.
- No source code changes.
- No frontend model special-cases.
- No payment, settlement, account, ACL, record-rule, or manifest changes.

## Input

- `product_entry_openability_screen_v1.md`:
  upstream product maintenance entry is openable for the purchase-manager chain.
- Read-only Odoo shell probe on `sc_demo`:
  classified active users across `purchase.group_purchase_manager`,
  `smart_construction_custom.group_sc_role_payment_manager`, and
  `smart_construction_core.group_sc_cap_finance_manager`.

## Probe Result

| Fact | Count |
| --- | ---: |
| purchase managers | 68 |
| payment managers | 8 |
| finance managers | 11 |
| purchase/payment overlap | 0 |
| purchase/finance overlap | 1 |

Representative payment-only examples:

- `wutao`
- `wennan`
- `lina`
- `duanyijun`
- `jiangyijiao`
- `shuiwujingbanren`
- `luomeng`
- `chenshuai`

Representative purchase-only examples:

- `legacy_10000051`
- `legacy_10000079`
- `legacy_10000036`
- `legacy_10000065`
- `legacy_10000067`

## Classification

- There is no account-level overlap between purchase-manager owners and
  payment-manager operators in current runtime facts.
- Therefore the operational path is not a single-account same-role chain.
- The system already carries both owner sets, so this is not a missing-owner
  defect.
- The path currently depends on explicit cross-role handoff between:
  - upstream purchase-manager accounts for product/purchase ownership
  - downstream payment-manager accounts for settlement/payment ownership
- A small amount of cross-capability proximity exists through finance-manager
  overlap, but not enough to collapse the path into one unified owner chain.

## Decision

- Do not change payment or settlement business code.
- Do not open a permission-governance batch from this result.
- Do not add frontend special-cases.
- The next low-cost question is whether the split is purely account-level or
  whether the same natural person already exists across upstream and downstream
  accounts, which would affect onboarding guidance rather than code changes.

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-18-CROSS-ROLE-HANDOFF-VERIFY-SCREEN.yaml`: PASS
- `DB_NAME=sc_demo make odoo.shell.exec` read-only cross-role handoff verify screen: PASS
- `git diff --check`: PASS

## Risk And Stop Decision

- Result: PASS.
- Stop condition: none in this screen.
- Risk: runtime onboarding still spans distinct account sets, so operational
  handoff guidance may still be necessary.
- Boundary: follow-up remains an onboarding/identity classification problem, not
  a payment/settlement semantic issue.

## Next Step

Open a low-cost same-person cross-account handoff screen:

- screen whether upstream purchase-manager and downstream payment-manager chains
  already overlap at the natural-person level via duplicated legacy/current
  accounts;
- keep payment, settlement, ACL, and frontend code frozen;
- stop before any implementation batch unless a real runtime handoff gap is
  proven.
