# P3 Gate Rules v0.1 (Draft)

## 0. Gate Purpose

Translate P3 reconciliation contracts into future CI/smoke checks.
No runtime implementation in this document.

## 1. MUST Rules

P3-GATE-001
- Statement: Derived reconciliation fields are not writable by users.
- Evidence / Check: static scan of model fields + runtime write guard in smoke.
- Failure Mode: write succeeds or missing guard.

P3-GATE-002
- Statement: Settlement cumulative only uses `approve/done` states.
- Evidence / Check: SQL/ORM filter check in smoke.
- Failure Mode: other states included in totals.

P3-GATE-003
- Statement: Payment requested cumulative uses explicit state set (submit/approve/approved/done).
- Evidence / Check: SQL/ORM filter check in smoke.
- Failure Mode: missing state or extra states included.

P3-GATE-004
- Statement: Payment paid cumulative only includes `done` state.
- Evidence / Check: SQL/ORM filter check in smoke.
- Failure Mode: any non-done records included.

P3-GATE-005
- Statement: Locked period ledgers are immutable after lock.
- Evidence / Check: runtime smoke reuses P2 PERIOD_LOCKED guard.
- Failure Mode: write/unlink allowed when period locked.

P3-GATE-006
- Statement: Settlement line must be bound to contract.
- Evidence / Check: runtime smoke reuses P2 SETTLEMENT_CONTRACT_REQUIRED guard.
- Failure Mode: settlement line created/updated without contract.

P3-GATE-007
- Statement: Payment submit requires attachments.
- Evidence / Check: runtime smoke reuses P2 PAYMENT_ATTACHMENTS_REQUIRED guard.
- Failure Mode: submit succeeds with zero attachments.

P3-GATE-008
- Statement: Key state transitions write audit events.
- Evidence / Check: audit query for event codes after transitions.
- Failure Mode: missing event_code in sc.audit.log.

P3-GATE-009
- Statement: Reason-required transitions enforce reason.
- Evidence / Check: runtime smoke reuses P2 AUDIT_REASON_REQUIRED guard.
- Failure Mode: transition succeeds without reason.

## 2. SHOULD Rules

P3-GATE-101
- Statement: Event codes must be in the dictionary.
- Evidence / Check: audit scan for unknown event_code.
- Failure Mode: unknown codes -> warn.

P3-GATE-102
- Statement: reconcile_delta < 0 raises warning.
- Evidence / Check: derived field check + warn output.
- Failure Mode: negative delta not reported.

P3-GATE-103
- Statement: settlement_amount_approved_cum > contract_amount_total raises warning.
- Evidence / Check: aggregate check.
- Failure Mode: over-contract not reported.

P3-GATE-104
- Statement: partner aggregates must match sum of record-level totals.
- Evidence / Check: aggregation consistency check.
- Failure Mode: mismatch not reported.

P3-GATE-105
- Statement: audit queries must support required dimensions.
- Evidence / Check: query contract verification (static).
- Failure Mode: dimension missing.

## 3. OPTIONAL Rules

P3-GATE-201
- Statement: trace_id correlates multi-step actions across models.
- Evidence / Check: optional correlation scan.
- Failure Mode: missing trace_id chain.

## 4. Future Gate Script Hooks

Planned script entry points (not implemented in this sprint):
- `scripts/ops/p3_runtime_smoke.py` (placeholder)
- SQL checklist for reconciliation aggregates (placeholder)
