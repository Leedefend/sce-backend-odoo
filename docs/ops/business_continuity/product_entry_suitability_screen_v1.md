# Product Entry Suitability Screen v1

## Batch

- Task: `ITER-2026-04-18-PRODUCT-ENTRY-SUITABILITY-SCREEN`
- Layer Target: Business Fact Screening
- Module: product entry suitability
- Module Ownership: customer-delivery business continuity
- Kernel or Scenario: scenario
- Backend Sub-Layer: business-fact layer
- Reason: product entry exposure exists; the remaining question is whether the
  visible native path is actually create-capable for the existing owner chain.

## Scope

- Screen only.
- Allowed outputs: this report, task contract, delivery context log.
- No source code changes.
- No frontend model special-cases.
- No payment, settlement, account, ACL, record-rule, or manifest changes.

## Input

- `product_entry_exposure_screen_v1.md`:
  purchase-manager chain can see `stock.menu_product_stock` and registry
  contains multiple `product.product` actions.
- Read-only Odoo shell probe on `sc_demo`:
  inspected the actual visible action `stock.action_product_stock_view` for
  representative purchase-manager owner `legacy_10000009`.

## Probe Result

Visible action under test:

| Field | Value |
| --- | --- |
| action xmlid | `stock.action_product_stock_view` |
| action name | `Stock` |
| res_model | `product.product` |
| view_mode | `tree,form` |
| target | `current` |
| domain | `[('detailed_type', '=', 'product')]` |
| context | `{'default_detailed_type': 'product'}` |
| probe user create right | yes |
| probe user write right | yes |

Explicit action-bound views:

| Mode | XMLID | View Type |
| --- | --- | --- |
| `tree` | `stock.product_product_stock_tree` | `tree` |

## Classification

- The currently visible native path is not merely a read-only report stub:
  it points to `product.product`, runs in current window, and the probe user
  has create/write authority on the target model.
- The action also carries `view_mode = tree,form`, so the route is intended to
  support maintenance flow rather than a pure analytical dashboard.
- However, the action explicitly binds only a tree view in `action.views`.
  Form usage therefore relies on default view fallback rather than an explicit
  action-level form binding.
- This means suitability is strongly indicated, but final openability of the
  maintenance path is not yet fully proven by this metadata-only screen.

## Decision

- Do not change payment or settlement business code.
- Do not add frontend special-cases.
- Do not open a governance batch from this result.
- Continue with one narrower low-cost screen to verify product entry
  openability/create flow under the existing native action path.

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-18-PRODUCT-ENTRY-SUITABILITY-SCREEN.yaml`: PASS
- `DB_NAME=sc_demo make odoo.shell.exec` read-only product entry suitability screen: PASS
- `git diff --check`: PASS

## Risk And Stop Decision

- Result: PASS.
- Stop condition: none in this screen.
- Risk: action metadata suggests a valid maintenance path, but explicit form
  binding is not yet proven on this screen.
- Boundary: if the next screen shows create/open requires a hidden or special
  path outside the visible native action, that becomes an exposure issue to
  classify before any implementation.

## Next Step

Open a low-cost product entry openability screen:

- verify whether `stock.action_product_stock_view` can naturally lead to a
  create-capable maintenance flow for the purchase-manager owner chain;
- verify whether that maintained product fact can hand off into the existing
  purchase-to-settlement runtime path without frontend branching;
- stop before any governance or implementation batch unless a real native-entry
  gap is proven.
