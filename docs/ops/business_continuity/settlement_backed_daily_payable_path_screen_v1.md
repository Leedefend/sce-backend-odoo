# Settlement-Backed Daily Payable Path Screen v1

## Batch

- Task: `ITER-2026-04-18-SETTLEMENT-BACKED-DAILY-PAYABLE-PATH-SCREEN`
- Layer Target: Business Fact Screening
- Module: settlement-backed daily payable path
- Module Ownership: customer-delivery business continuity
- Kernel or Scenario: scenario
- Backend Sub-Layer: business-fact layer
- Reason: no-contract/no-settlement daily payment is operable; the next daily business path must be diagnosed from backend business facts before any high-risk payment or settlement implementation.

## Scope

- Screen only.
- Allowed outputs: this report, task contract, delivery context log.
- No source code changes.
- No frontend model special-cases.
- No payment, settlement, account, ACL, record-rule, or manifest changes.

## Read-Only Probe Result

Current persistent business facts in `sc_demo`:

| Fact | Count |
| --- | ---: |
| `purchase.order` | 0 |
| `purchase.order.line` | 0 |
| `product.product` | 0 |
| `sc.settlement.order` | 0 |
| `sc.settlement.order.line` | 0 |
| settlement-backed `payment.request` | 0 |
| done settlement-backed `payment.request` | 0 |
| `payment.ledger` for settlement-backed payments | 0 |

Existing real data still consists of imported payment and ledger facts:

| Fact | Count |
| --- | ---: |
| `payment.request` | 30102 |
| `payment.ledger` | 12194 |

No persistent procurement source, settlement order, settlement line, or
settlement-backed payment carrier currently exists in the runtime database.

## Rollback-Only Probe Result

The probe created a complete temporary settlement-backed payable chain and
rolled it back at the end:

| Step | Result |
| --- | --- |
| Create project, contract, product, purchase order | PASS |
| Create settlement order and settlement line | PASS |
| Settlement `amount_total` from line | `100.0` |
| `settlement.action_submit()` | state `submit` |
| `settlement.action_approve()` | state `approve` |
| Create payment request linked to settlement | PASS |
| `payment.action_submit()` | state `submit` |
| tier approval path | state `approved` |
| payment ledger creation | PASS |
| `payment.action_done()` | state `done` |
| settlement remaining amount after payment | `60.0` |
| rollback clean | PASS |

Rollback integrity:

| Model | Before | After |
| --- | ---: | ---: |
| `purchase.order` | 0 | 0 |
| `purchase.order.line` | 0 | 0 |
| `product.product` | 0 | 0 |
| `sc.settlement.order` | 0 | 0 |
| `sc.settlement.order.line` | 0 | 0 |
| `payment.request` | 30102 | 30102 |
| `payment.ledger` | 12194 | 12194 |

## Classification

- Runtime behavior is operable when the required backend business facts exist:
  procurement source, settlement order, settlement line, selected settlement
  payment request, approval, ledger, and done all completed in rollback.
- The current blocker is not payment or settlement business logic.
- The current blocker is missing persistent source facts for the settlement-backed
  path: no product, no purchase order, no settlement order, no settlement line,
  and no settlement-backed payment records exist in `sc_demo`.
- This is not a frontend issue. Frontend must remain a generic semantic consumer
  and must not add model-specific bypass behavior.
- This screen does not justify changing `*payment*`, `*settlement*`, `*account*`,
  ACL, record rules, manifest, or frontend code.

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-18-SETTLEMENT-BACKED-DAILY-PAYABLE-PATH-SCREEN.yaml`: PASS
- `DB_NAME=sc_demo make odoo.shell.exec rollback-only settlement-backed daily payable path screen`: PASS
- First probe attempt found `odoo` service stopped before Odoo shell startup; `make up` restored the dev service and the same probe then passed.
- `git diff --check`: pending final run.

## Risk And Stop Decision

- Result: PASS.
- Stop condition: none for this screen.
- Risk: the settlement-backed path is operable only after runtime facts are
  created; the active database has no persistent source facts for this path.
- Boundary: do not solve this by changing payment/settlement semantics or adding
  frontend model special-cases.

## Next Step

Open the next low-cost screen for source fact materialization readiness:

- classify whether procurement product, purchase order, settlement order, and
  settlement line facts should come from existing legacy sources, install-time
  seed, or user-created runtime operations;
- do not replay or write persistent data until the source-of-truth and rollback
  path are declared in a dedicated task;
- if the next task requires data replay, create a separate authorized
  business-fact replay batch with an exact path and verification allowlist.
