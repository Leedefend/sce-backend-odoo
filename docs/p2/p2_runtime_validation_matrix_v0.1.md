# P2 Runtime Validation Matrix v0.1

Scope: P2 runtime execution control smoke validation (no demo data, minimal records).

| Capability | Precondition | Action | Expected Error Code / State | Expected Audit Event |
| --- | --- | --- | --- | --- |
| Task readiness | Project + WBS + task in draft | Direct `write(state=ready)` | `TASK_GUARD_DIRECT_STATE_WRITE` | task_ready/task_started/task_done/task_cancelled present |
| Task transitions | Task in draft and readiness satisfied | action_prepare_task -> action_start_task -> action_mark_done -> action_cancel_task(reason) | state: ready/in_progress/done/cancelled | task_ready, task_started, task_done, task_cancelled |
| Progress immutability | Progress entry in draft | Direct `write(state=submitted)` | `PROGRESS_GUARD_DIRECT_STATE_WRITE` | progress_submitted/progress_reverted present |
| Progress immutability | Progress entry submitted | `write(note=...)` or `unlink()` | `PROGRESS_GUARD_IMMUTABLE` | progress_submitted |
| Progress revert reason | Progress entry submitted | action_revert_progress(no reason) | `AUDIT_REASON_REQUIRED` | progress_reverted (after reasoned revert) |
| Ledger lock | Period locked | ledger create/write/unlink | `PERIOD_LOCKED` | period_locked/period_unlocked present |
| Ledger unlock reason | Period locked | action_unlock_period(no reason) | `AUDIT_REASON_REQUIRED` | period_unlocked (after reasoned unlock) |
| Contract link required | Settlement line without contract | create line without contract | `SETTLEMENT_CONTRACT_REQUIRED` | contract_bound/contract_unbound present |
| Contract link mismatch | Settlement line with contract from other project | create line with mismatched contract | `SETTLEMENT_CONTRACT_MISMATCH` | contract_bound/contract_unbound |
| Contract unbind reason | Settlement line with contract | action_unbind_contract(no reason) | `AUDIT_REASON_REQUIRED` | contract_unbound (after reasoned unbind) |
| Payment attachments | Payment request without attachments | action_submit | `PAYMENT_ATTACHMENTS_REQUIRED` | payment_submitted/payment_approved/payment_paid present |
| Payment approve tier | Payment request in submit, not validated | action_on_tier_approved | `PAYMENT_TIER_INCOMPLETE` | payment_approved |
| Payment direct state | Payment request | Direct `write(state=submit)` | `PAYMENT_GUARD_DIRECT_STATE_WRITE` | payment_submitted |
| Payment reject reason | Payment request in submit | action_on_tier_rejected(no reason) | `AUDIT_REASON_REQUIRED` | payment_submitted |
| Payment lifecycle | Payment request validated + ledger | action_submit -> action_on_tier_approved -> action_done | state: submit/approved/done | payment_submitted, payment_approved, payment_paid |
