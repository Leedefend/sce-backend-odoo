# Product Entry Exposure Screen v1

## Batch

- Task: `ITER-2026-04-18-PRODUCT-ENTRY-EXPOSURE-SCREEN`
- Layer Target: Business Fact Screening
- Module: product entry exposure
- Module Ownership: customer-delivery business continuity
- Kernel or Scenario: scenario
- Backend Sub-Layer: business-fact layer
- Reason: the upstream purchase-manager owner chain exists; the remaining
  question is whether it already has a native product entry suitable for
  starting the source-fact path.

## Scope

- Screen only.
- Allowed outputs: this report, task contract, delivery context log.
- No source code changes.
- No frontend model special-cases.
- No payment, settlement, account, ACL, record-rule, or manifest changes.

## Input

- `runtime_handoff_exposure_verify_screen_v1.md`:
  upstream/downstream ownership split exists across purchase-manager and
  payment-manager chains.
- Read-only Odoo shell probe on `sc_demo`:
  inspected visible native `product.product` menus and actions for
  representative purchase-manager owner `legacy_10000009` (`吴涛`).

## Probe Result

Probe user: `legacy_10000009`

Visible native `product.product` menus:

| Menu | XMLID | Action |
| --- | --- | --- |
| `Inventory/Reporting/Stock` | `stock.menu_product_stock` | `stock.action_product_stock_view` |

Visible native `product.product` actions in registry:

| Action | XMLID | View Mode |
| --- | --- | --- |
| `Product Variants` | `purchase.product_product_action` | `tree,kanban,form,activity` |
| `Product Variants` | `product.product_normal_action` | `tree,form,kanban,activity` |
| `Product Variants` | `product.product_variant_action` | `tree,form` |
| `Product Variants` | `product.product_normal_action_sell` | `kanban,tree,form,activity` |
| `Product Variants` | `stock.stock_product_normal_action` | `tree,form,kanban` |
| `Products` | `stock.act_product_location_open` | `tree,form` |
| `Stock` | `stock.action_product_stock_view` | `tree,form` |

## Classification

- The purchase-manager owner chain is not blocked by missing `product.product`
  action definitions. Native actions already exist.
- At least one native product-related menu is visible to the representative
  owner chain.
- The currently observed visible menu is a stock-reporting path
  (`Inventory/Reporting/Stock`), not yet a clearly verified product-maintenance
  entry dedicated to creating the minimal upstream source fact.
- Therefore the remaining uncertainty is not model authority and not missing
  product actions; it is entry suitability/openability for the actual
  maintenance workflow.

## Decision

- Do not change payment or settlement business code.
- Do not add frontend special-cases.
- Do not open a governance batch from this result.
- Continue with one more low-cost screen to verify whether the visible native
  product action path is suitable for opening or creating the minimal upstream
  product fact.

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-18-PRODUCT-ENTRY-EXPOSURE-SCREEN.yaml`: PASS
- `DB_NAME=sc_demo make odoo.shell.exec` read-only product entry exposure screen: PASS
- `git diff --check`: PASS

## Risk And Stop Decision

- Result: PASS.
- Stop condition: none in this screen.
- Risk: product action presence is confirmed, but the exact operator-suitable
  maintenance entry remains unverified.
- Boundary: if the next screen shows only reporting-style or hidden admin paths
  are usable, that becomes an exposure/onboarding issue to classify before any
  implementation.

## Next Step

Open a low-cost product entry suitability screen:

- verify whether the visible native product path can open a create-capable
  maintenance entry for the purchase-manager owner chain;
- verify whether this step can hand off naturally into the existing purchase and
  settlement runtime path without frontend branching;
- stop before any governance or implementation batch unless a real runtime
  exposure gap is proven.
