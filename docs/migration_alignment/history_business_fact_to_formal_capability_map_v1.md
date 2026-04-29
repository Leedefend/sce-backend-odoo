# History Business Fact To Formal Capability Map v1

Status: `READY`

Task: `ITER-2026-04-25-HISTORY-BUSINESS-FACT-CAPABILITY-MAP-001`

## Principle

The migration program must not decide user-facing pages from imported carrier
models.

The governing rule is:

- determine which business facts users continue to use in daily work
- strengthen the corresponding formal capabilities in the new system
- treat historical carrier models as source/audit/reconciliation layers only

In short:

- `legacy fact` decides **what capability must be completed**
- `formal capability` decides **what page the user should actually use**

## Mapping Matrix

| Historical Business Fact | Current Fact Sources | User Daily Intent | Formal Capability In New System | Delivery Form | Notes |
|---|---|---|---|---|---|
| Payment request lifecycle | `outflow_request_core`, workflow audit, downstream approval facts | submit / review / follow payment request progress | `payment.request` | runtime model + list/form + scene delivery | already promoted through `draft -> submit -> approved -> done` restoration |
| Historical paid completion | `actual_outflow_core`, downstream fact state sync, historical ledger evidence | view paid records, reconcile payment completion | `payment.ledger` | formal runtime ledger page | users should view `支付台账`, not `legacy actual outflow` carrier |
| Treasury movement / fund outflow view | `payment.request`, `payment.ledger`, treasury projection | track project fund movement and finance history | `sc.treasury.ledger` | projection page | should remain user-facing finance page |
| Receipt income facts | `legacy_receipt_income_fact` | view historical income by project/partner/category | future receipt / income ledger capability | projection or formal finance analysis page | temporary internal visibility allowed, not final user main page |
| Expense / deposit facts | `legacy_expense_deposit_fact` | view historical expense/deposit facts and reconcile with payments | future expense/deposit ledger capability | projection or finance operations page | temporary internal visibility allowed |
| Invoice tax facts | `legacy_invoice_tax_fact` | view tax/invoice historical facts for finance work | future invoice/tax capability | projection or formal invoice/tax page | do not keep raw `sc.legacy.invoice.tax.fact` as end-user page |
| Financing loan facts | `legacy_financing_loan_fact` | view financing history, loan trace, project-linked borrowing facts | future financing management capability | projection or financing ledger page | temporary internal visibility allowed |
| Fund daily snapshot facts | `legacy_fund_daily_snapshot_fact` | view historical daily fund status / management snapshots | future fund daily / treasury analysis capability | projection or dashboard scene | temporary internal visibility allowed |
| Approval trace facts | `legacy_workflow_audit` | audit why a record reached a state | internal audit only | internal audit page only | not a daily user capability |
| Migration staging / neutral member carriers | `sc.project.member.staging` and related migration artifacts | none | no direct user capability | carrier-only | must stay hidden from user navigation |

## Current Capability Status

### Already Formalized

- `payment.request`
- `payment.ledger`
- `sc.treasury.ledger`
- runtime line facts:
  - `payment.request.line`
  - `sc.receipt.invoice.line`

### Internal-Visible Transitional Layer

These facts may be visible to finance/internal users for audit or
reconciliation, but they are not the target end-state user capability:

- `sc.legacy.receipt.income.fact`
- `sc.legacy.expense.deposit.fact`
- `sc.legacy.invoice.tax.fact`
- `sc.legacy.financing.loan.fact`
- `sc.legacy.fund.daily.snapshot.fact`

### Remain Internal Only

- `sc.legacy.workflow.audit`
- migration recovery and staging carriers

## Product Rule

When a historical fact family proves that users still need a business
capability, the implementation sequence must be:

1. preserve and verify the historical facts
2. identify the formal runtime/projection capability that should own the user experience
3. upgrade the formal capability page
4. keep raw historical facts as internal evidence/support only

Do not invert the order by exposing the raw carrier as the user product.

## Rebuild Flow Guarantee

The current official rebuild flow is not allowed to stop at carrier/fact
replay. Historical facts that already have user-facing runtime carriers must be
projected into those runtime models before business usability is accepted.

The replay path must include projection and probe coverage for:

- `sc.settlement.adjustment`
- `sc.expense.claim`
- `sc.treasury.reconciliation`
- `sc.receipt.income`
- `sc.payment.execution`
- `sc.invoice.registration`
- `sc.financing.loan`
- `sc.general.contract`
- `sc.construction.diary`

Acceptance requires `history.business.usable.probe` to return
`history_business_usable_ready` with `gap_count=0`. A result of
`history_business_usable_visible_but_promotion_gaps` is not acceptable when the
gap points to a user-facing runtime model that carries historical business
data.

This is a rebuild-process guarantee, not just a one-time repair of one
database. If a rebuild bypasses the official replay flow and only imports
carrier/fact rows, the same usability failure can reappear and the run must be
treated as incomplete.

## Model Upgrade Impact Rule

Future iterations may promote a transitional carrier/projection model into a
formal system business model. That upgrade is allowed only when its migration
impact is explicitly reviewed and recorded.

Every such model upgrade must answer:

- Which historical fact sources feed the model.
- Which projection script writes the runtime records.
- Whether `_name`, table name, unique constraints, or `legacy_source_model`
  values change.
- Whether the projection remains idempotent after the model upgrade.
- Whether menus, access rules, record rules, and role surfaces still expose the
  records to the intended real users.
- Whether AR/AP, finance, workflow, and business-usable smoke baselines change.
- How old runtime rows are cleaned or migrated during rollback.

No model upgrade may be marked complete until the rebuild flow and
`history.business.usable.probe` have been updated to cover the new model
contract.

## Current Delivery Implications

### Finance Daily Use

Daily finance use should converge on:

- `payment.request`
- `payment.ledger` (`支付台账`)
- `sc.treasury.ledger` (`资金台账`)

### Internal Finance Audit / Reconciliation

Internal finance operations may temporarily use:

- `历史财务事实（内部）`
  - `历史收款收入`
  - `历史费用/保证金`
  - `历史发票税额`
  - `历史融资借款`
  - `历史资金日报`

### Exclusions

The following should not be turned into user main entries:

- `sc.legacy.workflow.audit`
- migration staging pages
- recovery evidence carriers

## Next Batch Guidance

`Batch-History-Capability-Promotion-C`

Target:

- use this mapping to decide which formal finance capabilities should be
  enhanced next
- current delivered capability:
  - `payment.request(type=receive)` now has formal entry `收款申请`
  - `sc.treasury.ledger(direction=in)` now has formal entry `收款台账`
  - `sc.receipt.invoice.line` now has formal entry `收款发票台账`
  - `sc.legacy.financing.loan.fact` now has formal delivery entry `融资台账`
  - `sc.legacy.fund.daily.snapshot.fact` now has formal delivery entry `资金日报`
- next priorities:
  - tax formal capability
  - treasury analysis capability

Not allowed:

- adding more user-facing raw `sc.legacy.*` pages instead of strengthening formal capabilities
