# Historical Business Data Model Alignment Plan

## Boundary

- Phase 1 replay/import only restores historical facts and source evidence.
- Phase 2 user-usable initialization must project those facts into current formal business models.
- User-visible pages are accepted only when the formal model has data, the user can read it, and the model/view framework audit passes.

## Current Baseline

| gate | command | current result |
|---|---|---|
| Formal backfill carrying | `make verify.formal_business_backfill.audit DB_NAME=sc_demo` | PASS, `gap_count=0` |
| User-visible fact alignment | `make verify.user_visible_business_fact_alignment DB_NAME=sc_demo` | PASS, `verified_count=55`, `errors=[]` |
| Model/view framework | `make verify.model_view.standardization.plan DB_NAME=sc_demo MODEL_VIEW_AUDIT_LOGIN=wutao` | PASS, `P0=0`, `P1=0`, `OK=116` |
| User-usable runtime | `make history.business.usable.probe DB_NAME=sc_demo` | PASS, `gap_count=0` |

## Added Alignment Scope

`project.cost.ledger` is now part of the historical business data alignment scope:

| source fact | formal visible model | acceptance count in `sc_demo` |
|---|---|---:|
| `sc.payment.execution` | `project.cost.ledger` | 12363 |
| `sc.expense.claim` | `project.cost.ledger` | 27991 |
| `sc.subcontract.settlement` | `project.cost.ledger` | 52 |
| `sc.settlement.order` | `project.cost.ledger` | 2 |

The total user-visible cost ledger coverage is 40408 runtime fact rows, with `wutao` read permission parity.

## Rebuild Rule

Any historical replay intended for business use must run:

```bash
make history.business.usable.init DB_NAME=<db>
```

That stage now includes `project_cost_ledger_projection_write.py`, so cost ledger pages are rebuilt from backend facts rather than relying on a one-off local projection.
