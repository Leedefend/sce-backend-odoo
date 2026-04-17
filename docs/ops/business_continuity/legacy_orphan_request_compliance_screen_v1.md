# Legacy Orphan Request Compliance Screen v1

## Purpose

New payable settlement submit/approve is blocked by existing payment requests
without settlement links. This screen counts and classifies the affected
population before replay or lifecycle changes.

The screen used read-only database queries and rolled back the shell
transaction.

## Result

Payment request population:

- total `payment.request`: 30102
- linked to `sc.settlement.order`: 0
- missing `settlement_id`: 30102

Missing-settlement requests by state:

- `done`: 12194
- `draft`: 17908

Ledger evidence:

- total `payment.ledger`: 12194
- missing-settlement requests with ledger: 12194
- done missing-settlement requests with ledger: 12194
- missing-settlement requests without ledger: 17908

## Field Evidence

Existing imported approval fields on `payment.request`:

- `legacy_approval_state`
- `legacy_approval_audit_count`
- `legacy_approval_approved_count`
- `legacy_approval_last_at`
- `legacy_approval_summary`

Existing settlement fields on `payment.request` include:

- `settlement_id`
- `settlement_amount_total`
- `settlement_amount_payable`
- `settlement_paid_amount`
- `settlement_remaining_amount`
- `settlement_compliance_state`
- `settlement_match_blocked`
- `settlement_match_warn`

## Classification

All payment requests currently miss the new-system settlement carrier.

The population splits into two materially different groups:

- 12194 requests are already `done` and have ledger records. These have strong
  downstream business facts and can be treated as completed historical payable
  facts.
- 17908 requests are still `draft` and have no ledger records. These should not
  be auto-promoted to completed facts without additional business evidence.

This confirms the user's earlier boundary: old audit completeness cannot be
required, but downstream business facts can establish approval/completion truth.

## Operational Impact

The current global three-way validation sees old missing-settlement requests and
blocks new settlement submit/approve. That means daily new-system operation is
blocked even when a newly created settlement order has correct source and line
amount facts.

## Next Batch

Open a replay candidate design batch:

- materialize settlement orders/lines for the 12194 completed requests with
  ledger evidence
- link completed requests and ledgers to reconstructed settlement facts where
  the project, partner, contract, and amount are deterministic
- keep the 17908 draft/no-ledger requests out of completed replay unless later
  evidence is found
- separately decide whether validation should ignore draft/no-ledger historical
  requests or whether they need draft settlement carriers
