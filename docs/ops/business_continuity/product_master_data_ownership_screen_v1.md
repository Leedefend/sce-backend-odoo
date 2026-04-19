# Product Master-Data Ownership Screen v1

## Batch

- Task: `ITER-2026-04-18-PRODUCT-MASTER-DATA-OWNERSHIP-SCREEN`
- Layer Target: Business Fact Screening
- Module: product master-data ownership
- Module Ownership: customer-delivery business continuity
- Kernel or Scenario: scenario
- Backend Sub-Layer: business-fact layer
- Reason: runtime source ownership screening showed the payment operator can
  create purchase and settlement records but cannot create products, so the
  next question is whether an existing role already owns this upstream step.

## Scope

- Screen only.
- Allowed outputs: this report, task contract, delivery context log.
- No source code changes.
- No frontend model special-cases.
- No payment, settlement, account, ACL, record-rule, or manifest changes.

## Input

- `runtime_source_ownership_screen_v1.md`:
  `wutao` can create `purchase.order` and `sc.settlement.order` but cannot
  create or maintain `product.product`.
- Read-only Odoo shell probe on `sc_demo`:
  scanned active users for `product.product` create/write authority and checked
  whether those users already belong to purchase or payment ownership chains.

## Runtime Ownership Result

- Active users with `product.product` create/write authority: `68`
- All detected owners also have:
  - `purchase.group_purchase_user = true`
  - `purchase.group_purchase_manager = true`
- None of the detected owners are in:
  - `smart_construction_custom.group_sc_role_payment_manager`

Representative examples from the read-only probe:

| Login | Product create/write | Purchase manager | Payment manager |
| --- | --- | --- | --- |
| `admin` | yes | yes | no |
| `legacy_10000009` (`吴涛`) | yes | yes | no |
| `legacy_a74a3dd36c004a4b8491675919c6be4c` (`李娜`) | yes | yes | no |
| `legacy_2afb101f2d3d41058b33517895db14f9` (`税务经办人`) | yes | yes | no |

## Classification

- Existing ownership already exists for the missing product master-data step.
- The owning chain is the native purchase-management authority surface, not the
  payment-manager runtime role used in the no-contract payment continuity probe.
- Therefore the upstream handoff is operationally split across existing roles:
  - product master-data creation/maintenance: purchase-manager chain
  - purchase order and settlement order operation: already available in the
    payment continuity runtime path
- This is not a missing payment or settlement semantic rule.
- This also does not require a new product-specific governance batch based on
  current evidence, because an existing owner set is present already.

## Decision

- Do not change payment or settlement business code.
- Do not add frontend special-cases.
- Do not open a permission-governance batch from this result.
- The remaining question is procedural and exposure-focused:
  whether the existing purchase-manager product step can hand off cleanly into
  the already exposed purchase-to-settlement path used by the payable flow.

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-18-PRODUCT-MASTER-DATA-OWNERSHIP-SCREEN.yaml`: PASS
- `DB_NAME=sc_demo make odoo.shell.exec` read-only product master-data ownership screen: PASS
- `git diff --check`: PASS

## Risk And Stop Decision

- Result: PASS.
- Stop condition: none in this screen.
- Risk: runtime ownership is split across existing roles, so the next issue is
  role handoff/onboarding rather than missing model authority.
- Boundary: if the handoff check later shows menu/action exposure mismatch for
  the purchase-manager chain, that should still be screened before any
  permission or frontend change.

## Next Step

Open a low-cost runtime handoff exposure verify screen:

- verify that the existing purchase-manager ownership chain has native product
  entry exposure suitable for creating the minimal upstream source fact;
- verify that the handoff from purchase-manager product creation to the
  existing purchase/settlement runtime path needs no frontend branching;
- stop before any governance batch unless the exposure check finds a real
  runtime authority gap.
