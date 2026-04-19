# Runtime Handoff Exposure Verify Screen v1

## Batch

- Task: `ITER-2026-04-18-RUNTIME-HANDOFF-EXPOSURE-VERIFY-SCREEN`
- Layer Target: Business Fact Screening
- Module: runtime handoff exposure and ownership split
- Module Ownership: customer-delivery business continuity
- Kernel or Scenario: scenario
- Backend Sub-Layer: business-fact layer
- Reason: existing product owners were found, so the next question is whether
  the upstream owner has native entry exposure and whether the downstream path
  is a normal role handoff instead of a semantic gap.

## Scope

- Screen only.
- Allowed outputs: this report, task contract, delivery context log.
- No source code changes.
- No frontend model special-cases.
- No payment, settlement, account, ACL, record-rule, or manifest changes.

## Input

- `product_master_data_ownership_screen_v1.md`:
  existing product ownership already exists in the purchase-manager chain.
- Read-only Odoo shell probe on `sc_demo`:
  inspected representative purchase-manager owner `legacy_10000009` (`吴涛`)
  for product, purchase, and settlement write access plus bounded native menu
  visibility.

## Probe Result

Probe user: `legacy_10000009` (`吴涛`)

| Fact | Value |
| --- | --- |
| `purchase.group_purchase_manager` | yes |
| `smart_construction_custom.group_sc_role_payment_manager` | no |
| `product.product.create/write` | yes / yes |
| `purchase.order.create/write` | yes / yes |
| `sc.settlement.order.create/write` | no / no |
| bounded `结算单` menu visible | yes |

The bounded probe did not find a product-named menu in the limited candidate
set, so product entry exposure is still not fully classified.

## Classification

- The current runtime path is split across existing roles:
  - purchase-manager chain owns product master-data and purchase-order creation
  - payment continuity path owns settlement-order creation and downstream
    payment lifecycle handling
- This is not evidence of a payment or settlement semantic defect.
- It is also not yet evidence of a permission-governance defect, because both
  upstream and downstream owners already exist in runtime facts.
- The remaining uncertainty is narrower:
  whether the purchase-manager chain has a clearly exposed native product entry
  suitable for starting the handoff without frontend branching or hidden-path
  reliance.

## Decision

- Do not change payment or settlement business code.
- Do not open a permission-governance batch from this result.
- Do not add frontend special-cases.
- Continue with one more low-cost screen focused only on native product entry
  exposure for the existing purchase-manager owner chain.

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-18-RUNTIME-HANDOFF-EXPOSURE-VERIFY-SCREEN.yaml`: PASS
- `DB_NAME=sc_demo make odoo.shell.exec` read-only runtime handoff exposure verify screen: PASS
- `git diff --check`: PASS

## Risk And Stop Decision

- Result: PASS.
- Stop condition: none in this screen.
- Risk: the operational split is understood, but the exact native product entry
  exposure for purchase-manager users remains unverified.
- Boundary: if the next screen finds that product maintenance exists only via a
  hidden or admin-only path, that becomes a new governance/exposure question
  and must still be screened before any implementation.

## Next Step

Open a low-cost product entry exposure screen:

- search native menu/action exposure for the existing purchase-manager owner
  chain;
- verify whether that product entry can start the upstream source-fact path
  without frontend branching;
- stop before any governance batch unless the exposure screen finds a real
  runtime authority or menu-exposure gap.
