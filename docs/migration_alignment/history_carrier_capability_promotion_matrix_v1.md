# History Carrier Capability Promotion Matrix v1

Status: `READY`

Task: `ITER-2026-04-25-HISTORY-CARRIER-CAPABILITY-MATRIX-001`

## Decision

Historical carrier models must be split into three classes instead of being
uniformly exposed to users:

1. `carrier-only`
2. `ops-visible internal`
3. `formal user capability`

The key rule is:

- users should not be sent directly to `sc.legacy.*` models for day-to-day work
- legacy facts remain the source layer
- user-facing delivery must be upgraded through native runtime models,
  projection models, or scene-owned pages

## Matrix

| Model / Fact Family | Current State | Delivery Class | User Menu Needed | Promotion Direction | Reason |
|---|---|---|---|---|---|
| `sc.legacy.workflow.audit` | view + action, no user menu | `carrier-only` | No | keep internal audit source | approval trace source, not daily user object |
| `sc.project.member.staging` | carrier-only | `carrier-only` | No | keep staging only | migration/staging ownership, not runtime business object |
| legacy contract / partner gap artifacts | scripts + audit only | `carrier-only` | No | keep migration-only | recovery evidence, not user capability |
| `sc.legacy.receipt.income.fact` | view only | `ops-visible internal` | Internal only | add internal action/menu if needed | historical income facts useful to ops/finance audit, not direct runtime transaction page |
| `sc.legacy.expense.deposit.fact` | view + action | `ops-visible internal` | Internal only | add internal menu under data/finance ops | support reconciliation and migration audit |
| `sc.legacy.invoice.tax.fact` | view + action | `ops-visible internal` | Internal only | add internal menu under data/finance ops | tax fact audit source, not daily operational object |
| `sc.legacy.financing.loan.fact` | view only | `ops-visible internal` | Internal only | add internal action/menu | financing history is useful for finance ops review |
| `sc.legacy.fund.daily.snapshot.fact` | view only | `ops-visible internal` | Internal only | add internal action/menu | management snapshot history is useful, but not raw end-user CRUD |
| `payment.request` | runtime model | `formal user capability` | Yes | already promoted | formal payment request capability |
| `payment.ledger` | runtime model | `formal user capability` | Yes | strengthen as payment-history ledger page | historical paid facts should land here for daily use |
| `sc.treasury.ledger` | projection with menu | `formal user capability` | Yes | continue as treasury-facing projection | user-facing treasury/finance analysis object |
| `sc.receipt.invoice.line` | runtime line fact | `formal user capability` | Indirect | deliver via receipt/payment pages | line-level business detail already belongs to runtime surface |
| `payment.request.line` | runtime line fact | `formal user capability` | Indirect | deliver via payment request pages | user-facing line detail already belongs to runtime surface |

## Formal Promotion Rules

### Rule A

`carrier-only` models must not receive user menus.

Allowed:

- replay
- audit
- migration diagnostics
- admin/internal investigation

Not allowed:

- user workbench navigation
- daily operations menu
- scene main entry

### Rule B

`ops-visible internal` models may receive internal menus, but only under
internal/data-center style navigation.

Allowed:

- implementation / migration / finance-ops review
- reconciliation support
- historical evidence lookup

Not allowed:

- becoming the user’s primary operational page
- being renamed as if they were native runtime objects

### Rule C

If a historical fact family is part of daily business continuation, it must be
promoted into a formal capability instead of exposing `sc.legacy.*`.

Preferred promotion targets:

- native runtime model
- projection model
- scene-owned delivery page

## Current Upgrade Priorities

### Priority 1

Payment continuity:

- source facts remain in historical assets / workflow audit / downstream fact artifacts
- user-facing delivery must stay on:
  - `payment.request`
  - `payment.ledger`
  - `sc.treasury.ledger`

### Priority 2

Finance history support:

- `legacy_receipt_income`
- `legacy_expense_deposit`
- `legacy_invoice_tax`
- `legacy_financing_loan`
- `legacy_fund_daily_snapshot`

These should become `ops-visible internal`, not direct user main-menu objects.

### Priority 3

Approval audit:

- `sc.legacy.workflow.audit`

Keep as carrier-only/internal audit source. Do not promote to user daily menu.

## Next Batch

`Batch-History-Capability-Promotion-A`

Target:

- add internal delivery entry for `ops-visible internal` models
- keep `carrier-only` hidden from user main navigation
- strengthen user-facing finance delivery around:
  - `payment.ledger`
  - `sc.treasury.ledger`

Not in scope:

- exposing raw `sc.legacy.*` as user main capability
- replacing native finance runtime pages with migration carrier pages

## Implementation Status

`Batch-History-Capability-Promotion-A` internal-entry implementation is now in place:

- internal finance menu:
  - `历史财务事实（内部）`
- included internal entries:
  - `历史收款收入`
  - `历史费用/保证金`
  - `历史发票税额`
  - `历史融资借款`
  - `历史资金日报`

Still intentionally excluded from user main menus:

- `sc.legacy.workflow.audit`
- migration staging / recovery carriers

Formal finance delivery strengthening is also now in place:

- `payment.ledger`
  - renamed user-facing delivery to `支付台账`
  - added search/group capability
  - remains under `财务账款`
- `sc.treasury.ledger`
  - kept as formal user capability
  - moved under `财务账款`
  - added search/group capability
