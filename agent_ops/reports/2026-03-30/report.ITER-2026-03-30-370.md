# ITER-2026-03-30-370 Report

## Summary

- Determined treasury-ledger ownership from production code, tests, and live facts.
- Confirmed that production currently implements `付款记录` generation, but does not implement an equivalent treasury-ledger generation trigger.
- Confirmed that tests treat `sc.treasury.ledger` as a projection fact that is manually seeded inside test setup rather than produced by a real upstream production action.

## Changed Files

- `agent_ops/tasks/ITER-2026-03-30-370.yaml`
- `agent_ops/reports/2026-03-30/report.ITER-2026-03-30-370.md`
- `agent_ops/state/task_results/ITER-2026-03-30-370.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-370.yaml` -> PASS

## Ownership Findings

### A. Production behavior that exists today

- `payment.request.action_done()` produces audit/evidence transitions.
- `payment.request._ensure_payment_ledger()` exists and is the explicit production helper for generating `payment.ledger`.
- `payment.ledger.create()` is guarded and only allowed through the payment-request path.

This means the production ownership of `付款记录` is explicit and implemented.

### B. Treasury-ledger behavior that does **not** exist in production

- `sc.treasury.ledger` model exists and is guarded by `allow_ledger_auto`.
- But the audited production code does not expose a matching upstream helper such as:
  - `_ensure_treasury_ledger()`
  - or a settlement/payment completion hook that creates treasury rows

### C. What tests are actually encoding

- `test_p0_ledger_gate.py`
- `test_p0_finance_aggregate_gate.py`

Both tests create treasury rows manually with:

- `env["sc.treasury.ledger"].with_context(allow_ledger_auto=True).create(...)`

So the tests do **not** prove an implemented production trigger.
They only prove:

- the treasury model exists
- ACL / record rules / aggregate reads behave as expected once rows already exist

## Governance Conclusion

- Current ownership is asymmetric by design or by incomplete implementation:
  - `付款记录`: owned by payment completion flow and implemented
  - `资金台账`: only modeled and permissioned, but not bound to a confirmed production-generation action

- Therefore the right next corrective question is not:
  - “where should we seed another row?”

- It is:
  - “which business event owns treasury-ledger generation?”
    - payment completion
    - settlement completion
    - finance posting
    - or explicit non-goal / deferred projection

## Risk Analysis

- This batch remains low-risk because it is audit-only.
- But the conclusion is governance-significant:
  - any real fix now requires entering the finance trigger chain intentionally
  - that crosses the current low-risk continuation boundary

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-30-370.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-30/report.ITER-2026-03-30-370.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-30-370.json`

## Next Suggestion

- Stop the current low-risk chain here.
- Open a finance-governed design/implementation batch that first declares treasury-ledger ownership explicitly.
- That batch should choose one path before any code change:
  - bind treasury generation to `payment.request.action_done`
  - bind it to `settlement` completion
  - bind it to a separate finance-posting flow
  - or formally mark native `资金台账` as deferred from demo-ready scope
