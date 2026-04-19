# Product Entry Openability Screen v1

## Batch

- Task: `ITER-2026-04-18-PRODUCT-ENTRY-OPENABILITY-SCREEN`
- Layer Target: Business Fact Screening
- Module: product entry openability
- Module Ownership: customer-delivery business continuity
- Kernel or Scenario: scenario
- Backend Sub-Layer: business-fact layer
- Reason: suitability screening showed the visible action metadata points to a
  maintenance path; this screen verifies whether the native path is actually
  openable and create-capable for the existing purchase-manager owner chain.

## Scope

- Screen only.
- Allowed outputs: this report, task contract, delivery context log.
- No source code changes.
- No frontend model special-cases.
- No payment, settlement, account, ACL, record-rule, or manifest changes.

## Input

- `product_entry_suitability_screen_v1.md`:
  `stock.action_product_stock_view` points to `product.product` with
  `view_mode=tree,form`, and the probe user has create/write rights.
- Read-only Odoo shell probe on `sc_demo`:
  resolved the actual form-view payload and simulated default/new record setup
  for representative purchase-manager owner `legacy_10000009`.

## Probe Result

Probe user: `legacy_10000009`

| Fact | Value |
| --- | --- |
| form payload type | `dict` |
| form arch present | yes |
| form payload preview | `form string="Product Variant" ...` |
| `default_get.detailed_type` | `product` |
| `default_get.sale_ok` | `true` |
| `default_get.purchase_ok` | `true` |
| `default_get.uom_id` | `1` |
| `new()._name` | `product.product` |
| `new().detailed_type` | `product` |
| `new().name` | `TMP_PRODUCT_OPENABILITY_PROBE` |

## Classification

- The visible native path is genuinely openable as a product-maintenance flow,
  not just a reporting shell.
- Under the existing purchase-manager owner chain, the native form arch can be
  resolved and product defaults can be initialized without hidden admin-only
  preparation.
- `new()` succeeds with the expected `product.product` target and product-type
  defaults, which is sufficient evidence for a minimal native create-capable
  upstream maintenance path in this low-cost screen.
- Therefore the upstream product step is operationally available through native
  runtime surfaces.

## Decision

- Do not change payment or settlement business code.
- Do not add frontend special-cases.
- Do not open a governance batch from this result.
- The remaining work is no longer to prove native product entry existence.
  The next step should verify or document the cross-role handoff from this
  upstream product/purchase chain into the already-proven settlement/payment
  path.

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-18-PRODUCT-ENTRY-OPENABILITY-SCREEN.yaml`: PASS
- `DB_NAME=sc_demo make odoo.shell.exec` read-only product entry openability screen: PASS
- `git diff --check`: PASS

## Risk And Stop Decision

- Result: PASS.
- Stop condition: none in this screen.
- Risk: native upstream entry is proven, but end-to-end business onboarding
  still spans multiple existing roles.
- Boundary: any follow-up remains a runtime onboarding/handoff question, not a
  payment/settlement semantic issue.

## Next Step

Open a low-cost cross-role handoff verify screen:

- verify how the native product/purchase owner chain hands off into the
  existing settlement/payment operator chain;
- keep all payment, settlement, ACL, and frontend code frozen;
- stop before any implementation batch unless a real runtime handoff gap is
  proven.
