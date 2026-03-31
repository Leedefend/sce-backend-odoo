# ITER-2026-03-30-369 Report

## Summary

- Audited why native `资金台账` is still empty in live `sc_demo`.
- Confirmed that the empty page is not explained by a lack of payment/settlement facts alone.
- Narrowed the root cause to a missing or intentionally unfulfilled treasury-ledger generation path in current production code.

## Changed Files

- `agent_ops/tasks/ITER-2026-03-30-369.yaml`
- `agent_ops/reports/2026-03-30/report.ITER-2026-03-30-369.md`
- `agent_ops/state/task_results/ITER-2026-03-30-369.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-369.yaml` -> PASS

## Audit Basis

### Static trigger-chain review

- `addons/smart_construction_core/models/projection/treasury_ledger.py`
  - model exists
  - manual create is blocked unless `allow_ledger_auto` is present
- `addons/smart_construction_core/views/projection/treasury_ledger_views.xml`
  - native page and menu exist
- searched production code for:
  - `env["sc.treasury.ledger"]`
  - `allow_ledger_auto`
  - treasury-ledger creation paths

### Live `sc_demo` facts checked

- `sc_treasury_ledger` row count = `0`
- `payment_request`:
  - `done_count = 40`
  - `with_settlement = 18`
  - `pay_count = 53`

This means the demo database already contains plenty of payment/settlement business facts, but they are not materializing into treasury-ledger rows.

## Result

### Core finding

- Outside tests, the audited production code does not currently expose a confirmed business trigger that creates `sc.treasury.ledger` rows.
- The model is present and guarded, but the live demo facts do not flow into it.
- Therefore the current native `资金台账` gap is better classified as:
  - `trigger-gap / unfulfilled native flow`
  - not merely `missing demo seed`

### Why this matters

- Seeding one row would hide the problem but would not explain the real business chain.
- A real corrective batch would need to enter one of the currently frozen high-risk finance areas:
  - `payment*`
  - `settlement*`
  - `account*`

## Risk Analysis

- Risk remains low in this batch because it is audit-only.
- But the next corrective step is not low-risk anymore.
- Any real treasury-ledger fulfillment batch would have to touch finance-generation logic or adjacent high-risk business triggers, which is outside the current safe continuation lane.

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-30-369.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-30/report.ITER-2026-03-30-369.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-30-369.json`

## Next Suggestion

- Stop the current low-risk native audit chain here.
- Open a dedicated finance-governed batch if you want `资金台账` to become truly usable.
- That next batch should explicitly decide one of:
  - implement the missing treasury-ledger generation trigger
  - define the intended upstream business action that must create it
  - or formally defer native `资金台账` out of the current demo-ready surface
