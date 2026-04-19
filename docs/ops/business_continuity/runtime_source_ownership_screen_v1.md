# Runtime Source Ownership Screen v1

## Batch

- Task: `ITER-2026-04-18-RUNTIME-SOURCE-OWNERSHIP-SCREEN`
- Layer Target: Business Fact Screening
- Module: runtime source ownership and entry exposure
- Module Ownership: customer-delivery business continuity
- Kernel or Scenario: scenario
- Backend Sub-Layer: business-fact layer
- Reason: the settlement-backed payable flow must now be treated as a runtime
  operation path, so the next question is whether the actual operator role
  already owns the required source-data entry points.

## Scope

- Screen only.
- Allowed outputs: this report, task contract, delivery context log.
- No source code changes.
- No frontend model special-cases.
- No payment, settlement, account, ACL, record-rule, or manifest changes.

## Inputs

- `source_fact_materialization_readiness_screen_v1.md`:
  missing procurement and settlement source facts are classified as runtime
  operations rather than legacy replay or install-time seed.
- `authority_runtime_upgrade_v1.md`:
  `wutao` is a real payment operator in `sc_demo` and passed the no-contract
  payment E2E after runtime authority alignment.
- Read-only Odoo shell probe on `sc_demo`:
  inspected `wutao` group membership, model access, and visible menu entries
  for `product.product`, `purchase.order`, and `sc.settlement.order`.

## Runtime Ownership Facts

Probe subject: `wutao`

| Group | Present |
| --- | --- |
| `smart_construction_custom.group_sc_role_payment_manager` | yes |
| `smart_construction_core.group_sc_cap_finance_manager` | yes |
| `purchase.group_purchase_user` | yes |
| `purchase.group_purchase_manager` | no |
| `product.group_product_manager` | no |

Model access for `wutao`:

| Model | Read | Create | Write | Delete |
| --- | --- | --- | --- | --- |
| `product.product` | yes | no | no | no |
| `purchase.order` | yes | yes | yes | yes |
| `sc.settlement.order` | yes | yes | yes | yes |

Visible menu entries found in the bounded probe:

| Menu | XMLID | Visible to `wutao` |
| --- | --- | --- |
| `结算单` | `smart_construction_core.menu_sc_settlement_order` | yes |

The visible `结算单` menu points to:

- action: `smart_construction_core.action_sc_settlement_order`
- action type: `ir.actions.act_window`
- menu groups:
  - `smart_construction_core.group_sc_cap_cost_read`
  - `smart_construction_core.group_sc_cap_finance_read`
  - `smart_construction_core.group_sc_cap_project_read`
  - `smart_construction_core.group_sc_cap_settlement_read`

## Classification

- The payment operator role already has runtime authority to create and maintain
  `purchase.order` and `sc.settlement.order`.
- Settlement entry exposure is already present for that role through the native
  `结算单` menu; this is not a frontend exposure gap.
- The missing runtime ownership is upstream of procurement transaction entry:
  `wutao` can read `product.product` but cannot create or maintain it.
- Therefore the settlement-backed payable path is only partially owned by the
  current payment operator role:
  - purchase-to-settlement operation: owned and operable
  - product master-data maintenance: not owned by the same role in current runtime facts

## Decision

- Do not open payment or settlement business-code implementation from this result.
- Do not add frontend special-cases to bypass missing product maintenance.
- The next uncertainty is narrow: who owns the minimal product master-data step
  required before the payment operator can start the purchase-to-settlement path.
- This remains a low-cost screening question unless the answer requires
  permission-governance or ACL changes.

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-18-RUNTIME-SOURCE-OWNERSHIP-SCREEN.yaml`: PASS
- `DB_NAME=sc_demo make odoo.shell.exec` read-only runtime source ownership screen: PASS
- `git diff --check`: PASS

## Risk And Stop Decision

- Result: PASS.
- Stop condition: none in this screen.
- Risk: source-path onboarding is still incomplete because product master-data
  ownership is not established for the payment operator role currently used in
  business continuity probes.
- Boundary: if the follow-up requires changing security groups, ACLs, or role
  inheritance, it must move into a dedicated authorized governance batch.

## Next Step

Open a low-cost product master-data ownership screen:

- identify whether an existing customer role already owns product creation and
  maintenance in `sc_demo`;
- identify whether that role can hand off naturally to the existing purchase and
  settlement path without frontend branching;
- if no existing role owns the minimal product step, stop and open a dedicated
  governance batch instead of changing payment or settlement code.
