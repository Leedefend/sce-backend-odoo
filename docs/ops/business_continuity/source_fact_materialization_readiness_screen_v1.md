# Source Fact Materialization Readiness Screen v1

## Batch

- Task: `ITER-2026-04-18-SOURCE-FACT-MATERIALIZATION-READINESS-SCREEN`
- Layer Target: Business Fact Screening
- Module: source fact materialization readiness
- Module Ownership: customer-delivery business continuity
- Kernel or Scenario: scenario
- Backend Sub-Layer: business-fact layer
- Reason: settlement-backed daily payable flow is runtime-operable in rollback;
  the remaining question is where missing source facts should come from before
  any persistent replay or write batch is opened.

## Scope

- Screen only.
- Allowed outputs: this report, task contract, delivery context log.
- No source code changes.
- No frontend model special-cases.
- No payment, settlement, account, ACL, record-rule, or manifest changes.

## Inputs

- `settlement_backed_daily_payable_path_screen_v1.md`:
  rollback-only chain reached settlement submit/approve, payment submit,
  approval, ledger, and done, then rolled back clean.
- `procurement_source_lifecycle_screen_v1.md`:
  product, purchase order, settlement order, and settlement line can be
  created in rollback, but there are no persistent records in `sc_demo`.
- `legacy_settlement_fact_existence_screen_v1.md`:
  no old settlement-order carrier exists; old/imported facts are payment and
  ledger oriented rather than settlement oriented.
- `imported_fact_usability_screen_v1.md`:
  do not fabricate settlement orders from ledger facts.
- Read-only Odoo shell probe on `sc_demo`:
  current source record counts remain zero and no `legacy_*` procurement or
  settlement carrier models are present in the current registry.

## Current Runtime Fact Counts

| Fact | Count |
| --- | ---: |
| `product.product` | 0 |
| `purchase.order` | 0 |
| `purchase.order.line` | 0 |
| `sc.settlement.order` | 0 |
| `sc.settlement.order.line` | 0 |
| `payment.request` | 30102 |
| `payment.ledger` | 12194 |

Legacy carrier presence in current registry:

| Legacy model | Count |
| --- | ---: |
| `sc.legacy.expense.deposit.fact` | 11167 |
| `sc.legacy.financing.loan.fact` | 318 |
| `sc.legacy.fund.daily.snapshot.fact` | 496 |
| `sc.legacy.invoice.tax.fact` | 5920 |
| `sc.legacy.receipt.income.fact` | 7220 |
| `sc.legacy.workflow.audit` | 79702 |

`legacy_purchase_like_models`: `[]`

## Source Classification

| Fact family | Legacy replay readiness | Install-time seed readiness | Runtime operation readiness | Classification |
| --- | --- | --- | --- | --- |
| `product.product` used by settlement-backed payable path | No deterministic legacy procurement/product carrier is declared in current registry or prior screens | Not suitable as a generic install seed because the needed product depends on customer procurement setup | Proven creatable in rollback and belongs to live procurement maintenance | Runtime operation |
| `purchase.order` / `purchase.order.line` | No deterministic legacy purchase-order source has been screened or mapped; current registry exposes no legacy procurement carrier | Not suitable as install seed because purchase orders are transactional documents | Proven creatable and confirmable in rollback | Runtime operation |
| `sc.settlement.order` | Legacy settlement existence screen found no old settlement carrier; payment/ledger facts must not be used to fabricate settlement orders | Not suitable as install seed because settlement orders are transaction facts with lifecycle state | Proven creatable and approvable in rollback when source facts exist | Runtime operation |
| `sc.settlement.order.line` | No deterministic old settlement-line carrier exists; line amount cannot be reconstructed from payment/ledger alone without fabrication | Not suitable as install seed because line amount is transaction-specific | Proven creatable in rollback and is the real amount carrier | Runtime operation |

## Decision

- The settlement-backed daily payable path does not currently need payment or
  settlement semantic changes.
- It also does not justify install-time seed materialization for procurement or
  settlement transaction facts.
- No deterministic legacy source-of-truth has been established for procurement
  product, purchase order, settlement order, or settlement line materialization.
- The current ready path is user-created runtime operation:
  procurement product -> purchase order -> settlement order -> settlement line
  -> settlement-backed payment request -> ledger -> done.
- Historical payment and ledger facts must remain separate from any future
  settlement replay unless a dedicated legacy source screen establishes exact
  replay truth.

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-18-SOURCE-FACT-MATERIALIZATION-READINESS-SCREEN.yaml`: PASS
- `DB_NAME=sc_demo make odoo.shell.exec` read-only source fact materialization readiness screen: PASS
- `git diff --check`: PASS

## Risk And Stop Decision

- Result: PASS.
- Stop condition: none in this screen.
- Risk: customer runtime database still has zero persistent procurement and
  settlement source facts, so the path is ready only as an operator-created
  runtime flow, not as a preloaded baseline.
- Boundary: do not solve this by fabricating settlement carriers from imported
  payment or ledger facts, and do not add frontend-specific bypass behavior.

## Next Step

Open the next low-cost screen for runtime source ownership and onboarding:

- identify which role owns procurement product maintenance for this path;
- identify whether purchase order and settlement order entry are already
  exposed and operable for that role without frontend special-cases;
- keep payment and settlement business code frozen;
- if runtime ownership is unclear, stop before any persistent replay/write
  batch.
